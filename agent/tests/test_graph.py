import uuid
from typing import Any
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from agent.graph import agent
from agent.state import AgentState

SESSION_ID = "graph-session"


def _run(llm_responses: list[AIMessage], user_text: str) -> tuple[dict[str, Any], list[str]]:
    """LLM・記憶をモックにして compile 済みグラフを流し、(最終状態, 呼ばれた順) を返す。"""
    events: list[str] = []
    responses = iter(llm_responses)

    def fake_agent_llm(_messages: Any) -> AIMessage:
        events.append("agent")
        return next(responses)

    def fake_search(_session_id: str, _query: str) -> list[str]:
        events.append("memory_inject")
        return []

    def fake_save(_session_id: str, _content: str) -> None:
        events.append("memory_save")

    with (
        patch("agent.nodes._llm") as mock_llm,
        patch("agent.nodes.ChatBedrockConverse") as mock_summary_cls,
        patch("agent.nodes.search_memories", side_effect=fake_search),
        patch("agent.nodes.save_memory", side_effect=fake_save),
    ):
        mock_llm.invoke.side_effect = fake_agent_llm
        mock_summary_cls.return_value.invoke.return_value = AIMessage(content="要約")
        config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}
        final = agent.invoke(
            AgentState(messages=[HumanMessage(content=user_text)], session_id=SESSION_ID),
            config,
        )
    return final, events


class TestGraphWithoutTools:
    def test_runs_inject_then_agent_then_save(self) -> None:
        final, events = _run([AIMessage(content="こんにちは")], "hi")

        assert events == ["memory_inject", "agent", "memory_save"]
        assert final["messages"][-1].content == "こんにちは"


class TestGraphWithOneToolCall:
    def test_tool_node_runs_and_returns_to_agent(self) -> None:
        tool_call_message = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "calculate_calorie_deficit",
                    "args": {"current_weight_kg": 70.0, "target_weight_kg": 65.0},
                    "id": "call-1",
                }
            ],
        )
        final, events = _run([tool_call_message, AIMessage(content="計算しました")], "減量したい")

        assert events == ["memory_inject", "agent", "agent", "memory_save"]
        tool_messages = [m for m in final["messages"] if isinstance(m, ToolMessage)]
        assert len(tool_messages) == 1
        assert tool_messages[0].tool_call_id == "call-1"
        assert tool_messages[0].status != "error"
        assert final["messages"][-1].content == "計算しました"
        types = [type(m).__name__ for m in final["messages"]]
        assert types == ["HumanMessage", "AIMessage", "ToolMessage", "AIMessage"]
