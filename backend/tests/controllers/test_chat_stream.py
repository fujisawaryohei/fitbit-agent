import json
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from backend.controllers import chat as chat_module
from backend.models.message_role import MessageRole

AGENT_META = {"langgraph_node": "agent_node"}


def _agent_yielding(*items, error: Exception | None = None) -> MagicMock:
    async def _gen():
        for item in items:
            yield item
        if error is not None:
            raise error

    agent = MagicMock()
    agent.astream.return_value = _gen()
    return agent


async def _run(agent: MagicMock, conn=None) -> tuple[list[dict], MagicMock, MagicMock]:
    """_sse_generator を最後まで回し、(SSE のイベント, MessageRepository のモック, release のモック) を返す。"""
    conn = conn or MagicMock()
    repo = MagicMock()
    with patch.object(chat_module, "_agent", agent), \
         patch.object(chat_module, "MessageRepository", return_value=repo), \
         patch.object(chat_module, "release_connection") as release, \
         patch.object(chat_module, "set_fitbit_client"):
        events = [
            json.loads(raw.removeprefix("data: ").strip())
            async for raw in chat_module._sse_generator(
                message="こんにちは",
                user_id=7,
                chat_id=42,
                conn=conn,
                fitbit_client=MagicMock(),
            )
        ]
    return events, repo, release


def _saved_messages(repo: MagicMock) -> list:
    return [call.args[0] for call in repo.insert.call_args_list]


class TestSseChunks:
    async def test_string_content_is_emitted_as_chunks_then_done(self):
        agent = _agent_yielding(
            (AIMessage(content="こん"), AGENT_META),
            (AIMessage(content="にちは"), AGENT_META),
        )

        events, _, _ = await _run(agent)

        assert [e["type"] for e in events] == ["chunk", "chunk", "done"]
        assert [e["content"] for e in events[:2]] == ["こん", "にちは"]
        assert events[-1]["chat_id"] == 42
        assert all(e["session_id"] == "7" for e in events)

    async def test_list_content_blocks_are_joined_into_one_chunk(self):
        blocks = [
            {"type": "text", "text": "朝は"},
            {"type": "tool_use", "id": "x"},  # text が無いブロックは空文字として扱われる
            {"type": "text", "text": "元気です"},
            "dict ではないブロックは無視される",
        ]
        agent = _agent_yielding((AIMessage(content=blocks), AGENT_META))

        events, repo, _ = await _run(agent)

        assert [e["type"] for e in events] == ["chunk", "done"]
        assert events[0]["content"] == "朝は元気です"
        assert _saved_messages(repo)[-1].content == "朝は元気です"

    async def test_empty_content_emits_no_chunk(self):
        agent = _agent_yielding(
            (AIMessage(content=""), AGENT_META),
            (AIMessage(content=[]), AGENT_META),
            (AIMessage(content="あり"), AGENT_META),
        )

        events, _, _ = await _run(agent)

        assert [e["type"] for e in events] == ["chunk", "done"]
        assert events[0]["content"] == "あり"

    async def test_chunks_from_other_nodes_are_skipped(self):
        agent = _agent_yielding(
            (AIMessage(content="ツールの結果"), {"langgraph_node": "tool_node"}),
            (AIMessage(content="メタ無し"), {}),
            (AIMessage(content="応答"), AGENT_META),
        )

        events, repo, _ = await _run(agent)

        assert [e["content"] for e in events if e["type"] == "chunk"] == ["応答"]
        assert _saved_messages(repo)[-1].content == "応答"

    async def test_astream_receives_user_message_and_thread_id(self):
        agent = _agent_yielding()

        await _run(agent)

        args, kwargs = agent.astream.call_args
        assert args[0]["messages"][0].content == "こんにちは"
        assert args[0]["session_id"] == "7"
        assert kwargs["config"] == {"configurable": {"thread_id": "42"}}
        assert kwargs["stream_mode"] == "messages"


class TestSseSaving:
    async def test_saves_user_and_assistant_messages(self):
        agent = _agent_yielding(
            (AIMessage(content="こん"), AGENT_META),
            (AIMessage(content="にちは"), AGENT_META),
        )

        _, repo, _ = await _run(agent)

        saved = _saved_messages(repo)
        assert [(m.chat_id, m.role, m.content) for m in saved] == [
            (42, MessageRole.USER, "こんにちは"),
            (42, MessageRole.ASSISTANT, "こんにちは"),
        ]

    async def test_empty_response_saves_only_user_message(self):
        agent = _agent_yielding((AIMessage(content=""), AGENT_META))

        events, repo, _ = await _run(agent)

        saved = _saved_messages(repo)
        assert [(m.role, m.content) for m in saved] == [(MessageRole.USER, "こんにちは")]
        assert [e["type"] for e in events] == ["done"]


class TestSseErrorAndRelease:
    async def test_astream_error_yields_error_event_without_done(self):
        agent = _agent_yielding(
            (AIMessage(content="途中"), AGENT_META),
            error=RuntimeError("bedrock down"),
        )

        events, repo, _ = await _run(agent)

        assert [e["type"] for e in events] == ["chunk", "error"]
        assert "bedrock down" in events[-1]["content"]
        assert events[-1]["session_id"] == "7"
        # 例外のときは assistant の応答を保存しない
        assert [m.role for m in _saved_messages(repo)] == [MessageRole.USER]

    async def test_astream_error_before_any_chunk_yields_only_error(self):
        agent = _agent_yielding(error=ValueError("boom"))

        events, _, _ = await _run(agent)

        assert [e["type"] for e in events] == ["error"]

    async def test_connection_released_once_on_success(self):
        conn = MagicMock()

        _, _, release = await _run(_agent_yielding((AIMessage(content="a"), AGENT_META)), conn)

        release.assert_called_once_with(conn)

    async def test_connection_released_once_on_error(self):
        conn = MagicMock()

        _, _, release = await _run(_agent_yielding(error=RuntimeError("x")), conn)

        release.assert_called_once_with(conn)

    async def test_connection_released_when_consumer_stops_early(self):
        agent = _agent_yielding((AIMessage(content="a"), AGENT_META), (AIMessage(content="b"), AGENT_META))
        conn = MagicMock()
        with patch.object(chat_module, "_agent", agent), \
             patch.object(chat_module, "MessageRepository", return_value=MagicMock()), \
             patch.object(chat_module, "release_connection") as release, \
             patch.object(chat_module, "set_fitbit_client"):
            gen = chat_module._sse_generator(
                message="m", user_id=1, chat_id=1, conn=conn, fitbit_client=MagicMock()
            )
            await anext(gen)
            await gen.aclose()

        release.assert_called_once_with(conn)
