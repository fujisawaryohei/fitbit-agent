from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import END

from agent.nodes import (
    _extract_text,
    agent_node,
    memory_inject_node,
    memory_save_node,
    should_continue,
)
from agent.state import AgentState

SESSION_ID = "session-1"


def _state(messages: list[AnyMessage]) -> AgentState:
    return AgentState(messages=messages, session_id=SESSION_ID)


class TestExtractText:
    def test_string_is_returned_as_is(self) -> None:
        assert _extract_text("こんにちは") == "こんにちは"

    def test_text_blocks_are_joined_and_other_blocks_ignored(self) -> None:
        content = [
            {"type": "text", "text": "前半"},
            {"type": "tool_use", "id": "x", "name": "get_steps", "input": {}},
            {"type": "text", "text": "後半"},
        ]
        assert _extract_text(content) == "前半後半"

    def test_non_dict_items_in_list_are_ignored(self) -> None:
        assert _extract_text(["plain", {"type": "text", "text": "ok"}]) == "ok"

    def test_empty_list_returns_empty_string(self) -> None:
        assert _extract_text([]) == ""

    def test_other_types_are_stringified(self) -> None:
        assert _extract_text(123) == "123"


class TestShouldContinue:
    def test_ai_message_with_tool_calls_goes_to_tool_node(self) -> None:
        ai = AIMessage(
            content="",
            tool_calls=[{"name": "get_steps", "args": {}, "id": "call-1"}],
        )
        assert should_continue(_state([HumanMessage(content="歩数"), ai])) == "tool_node"

    def test_ai_message_without_tool_calls_ends(self) -> None:
        state = _state([HumanMessage(content="hi"), AIMessage(content="こんにちは")])
        assert should_continue(state) == END

    def test_last_message_not_ai_ends(self) -> None:
        assert should_continue(_state([HumanMessage(content="hi")])) == END


class TestAgentNode:
    def _invoke(self, messages: list[AnyMessage]) -> tuple[dict, list[AnyMessage]]:
        response = AIMessage(content="応答")
        with patch("agent.nodes._llm") as mock_llm:
            mock_llm.invoke.return_value = response
            result = agent_node(_state(messages))
        sent: list[AnyMessage] = mock_llm.invoke.call_args[0][0]
        return result, sent

    def test_returns_llm_response_in_messages(self) -> None:
        result, _ = self._invoke([HumanMessage(content="hi")])
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "応答"

    def test_injected_system_message_is_merged_into_single_leading_prompt(self) -> None:
        injected = SystemMessage(content="【過去の記憶】\n- 目標は60kg")
        _, sent = self._invoke(
            [injected, HumanMessage(content="こんにちは"), AIMessage(content="どうも")]
        )

        system_messages = [m for m in sent if isinstance(m, SystemMessage)]
        assert len(system_messages) == 1
        assert isinstance(sent[0], SystemMessage)
        assert "【過去の記憶】\n- 目標は60kg" in str(sent[0].content)

    def test_conversation_order_is_preserved_after_system_prompt(self) -> None:
        _, sent = self._invoke(
            [
                SystemMessage(content="注入"),
                HumanMessage(content="1"),
                AIMessage(content="2"),
                HumanMessage(content="3"),
            ]
        )
        assert [m.content for m in sent[1:]] == ["1", "2", "3"]
        assert [type(m) for m in sent[1:]] == [HumanMessage, AIMessage, HumanMessage]

    def test_without_injection_leading_system_prompt_is_still_sent(self) -> None:
        _, sent = self._invoke([HumanMessage(content="hi")])

        assert isinstance(sent[0], SystemMessage)
        assert str(sent[0].content).strip() != ""
        assert len(sent) == 2

    def test_multiple_injected_messages_are_all_included_in_order(self) -> None:
        _, sent = self._invoke(
            [
                SystemMessage(content="注入A"),
                SystemMessage(content="注入B"),
                HumanMessage(content="hi"),
            ]
        )
        prompt = str(sent[0].content)
        assert "注入A" in prompt and "注入B" in prompt
        assert prompt.index("注入A") < prompt.index("注入B")


class TestMemoryInjectNode:
    def test_searches_with_last_human_message_and_session_id(self) -> None:
        messages: list[AnyMessage] = [
            HumanMessage(content="古い質問"),
            AIMessage(content="答え"),
            HumanMessage(content="最新の質問"),
        ]
        with patch("agent.nodes.search_memories", return_value=[]) as mock_search:
            memory_inject_node(_state(messages))
        mock_search.assert_called_once_with(SESSION_ID, "最新の質問")

    def test_no_memories_returns_empty_messages(self) -> None:
        with patch("agent.nodes.search_memories", return_value=[]):
            result = memory_inject_node(_state([HumanMessage(content="hi")]))
        assert result == {"messages": []}

    def test_memories_become_single_system_message(self) -> None:
        with patch("agent.nodes.search_memories", return_value=["目標は60kg", "膝が悪い"]):
            result = memory_inject_node(_state([HumanMessage(content="hi")]))

        assert len(result["messages"]) == 1
        message = result["messages"][0]
        assert isinstance(message, SystemMessage)
        content = str(message.content)
        assert "【過去の記憶】" in content
        assert "- 目標は60kg" in content
        assert "- 膝が悪い" in content

    def test_without_human_message_searches_with_empty_query(self) -> None:
        with patch("agent.nodes.search_memories", return_value=[]) as mock_search:
            result = memory_inject_node(_state([AIMessage(content="こんにちは")]))
        mock_search.assert_called_once_with(SESSION_ID, "")
        assert result == {"messages": []}


class TestMemorySaveNode:
    def _run(
        self, summary: str | list, messages: list[AnyMessage]
    ) -> tuple[dict, MagicMock, MagicMock]:
        with (
            patch("agent.nodes.ChatBedrockConverse") as mock_cls,
            patch("agent.nodes.save_memory") as mock_save,
        ):
            mock_cls.return_value.invoke.return_value = AIMessage(content=summary)
            result = memory_save_node(_state(messages))
        return result, mock_cls.return_value, mock_save

    @pytest.mark.parametrize("summary", ["SKIP", "  SKIP\n", "\tSKIP "])
    def test_skip_does_not_save(self, summary: str) -> None:
        result, _, mock_save = self._run(summary, [HumanMessage(content="hi")])
        mock_save.assert_not_called()
        assert result == {"messages": []}

    def test_summary_is_saved_with_session_id(self) -> None:
        result, _, mock_save = self._run("目標は60kg", [HumanMessage(content="60kgにしたい")])
        mock_save.assert_called_once_with(SESSION_ID, "目標は60kg")
        assert result == {"messages": []}

    def test_summary_given_as_content_blocks_is_flattened(self) -> None:
        _, _, mock_save = self._run(
            [{"type": "text", "text": "要約"}], [HumanMessage(content="hi")]
        )
        mock_save.assert_called_once_with(SESSION_ID, "要約")

    def test_prompt_contains_user_and_assistant_but_not_system_or_tool(self) -> None:
        messages: list[AnyMessage] = [
            SystemMessage(content="システム注入の秘密"),
            HumanMessage(content="体重は70kg"),
            AIMessage(content="了解です"),
            ToolMessage(content="ツール結果の秘密", tool_call_id="call-1"),
        ]
        _, summary_llm, _ = self._run("SKIP", messages)

        prompt = summary_llm.invoke.call_args[0][0]
        assert "User: 体重は70kg" in prompt
        assert "Assistant: 了解です" in prompt
        assert "システム注入の秘密" not in prompt
        assert "ツール結果の秘密" not in prompt
