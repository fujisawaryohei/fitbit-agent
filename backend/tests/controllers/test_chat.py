import json
from unittest.mock import MagicMock, patch

# agent.nodes がモジュールロード時に ChatBedrockConverse を初期化するため、
# chat router のインポート前に差し替えておく
with patch("langchain_aws.ChatBedrockConverse", MagicMock()):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.controllers.chat import router as chat_router

_app = FastAPI()
_app.include_router(chat_router)


def _make_mock_user(expired: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = 1
    user.is_token_expired.return_value = expired
    user.access_token = "access-token"
    user.refresh_token = "refresh-token"
    return user


def _make_sse_stream(*chunks: str):
    """SSE チャンクを yield する AsyncMock を生成する。"""
    from langchain_core.messages import AIMessage

    async def _gen():
        for chunk in chunks:
            msg = AIMessage(content=chunk)
            yield msg, {"langgraph_node": "agent_node"}

    mock = MagicMock()
    mock.astream.return_value = _gen()
    return mock


class TestChatAuth:
    def test_no_cookie_returns_401(self):
        client = TestClient(_app)
        response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "認証が必要です" in response.json()["detail"]

    def test_unknown_user_returns_401(self):
        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_repo_class:
            mock_repo_class.return_value.find_by_fitbit_user_id.return_value = None
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "unknown-user")
            response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "ユーザーが見つかりません" in response.json()["detail"]

    def test_expired_token_returns_401(self):
        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_repo_class:
            mock_repo_class.return_value.find_by_fitbit_user_id.return_value = _make_mock_user(expired=True)
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "有効期限" in response.json()["detail"]


class TestChatStreaming:
    def test_sse_chunks_and_done_are_returned(self):
        user = _make_mock_user()
        agent = _make_sse_stream("今日", "の歩数は")

        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_user_repo, \
             patch("backend.controllers.chat.ChatRepository") as mock_chat_repo, \
             patch("backend.controllers.chat.MessageRepository"), \
             patch("backend.controllers.chat._agent", agent):

            mock_user_repo.return_value.find_by_fitbit_user_id.return_value = user
            mock_chat_repo.return_value.insert.return_value = 42

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}) as response:
                assert response.status_code == 200
                events = [
                    json.loads(line[6:])
                    for line in response.iter_lines()
                    if line.startswith("data: ")
                ]

        types = [e["type"] for e in events]
        assert "chunk" in types
        assert types[-1] == "done"

    def test_user_message_is_saved_to_db(self):
        user = _make_mock_user()
        agent = _make_sse_stream("応答")

        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_user_repo, \
             patch("backend.controllers.chat.ChatRepository") as mock_chat_repo, \
             patch("backend.controllers.chat.MessageRepository") as mock_msg_repo, \
             patch("backend.controllers.chat._agent", agent):

            mock_user_repo.return_value.find_by_fitbit_user_id.return_value = user
            mock_chat_repo.return_value.insert.return_value = 42

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

            insert_calls = mock_msg_repo.return_value.insert.call_args_list
            roles = [call.args[0].role for call in insert_calls]
            assert "user" in [str(r) for r in roles]

    def test_assistant_message_is_saved_to_db(self):
        user = _make_mock_user()
        agent = _make_sse_stream("8000歩です。")

        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_user_repo, \
             patch("backend.controllers.chat.ChatRepository") as mock_chat_repo, \
             patch("backend.controllers.chat.MessageRepository") as mock_msg_repo, \
             patch("backend.controllers.chat._agent", agent):

            mock_user_repo.return_value.find_by_fitbit_user_id.return_value = user
            mock_chat_repo.return_value.insert.return_value = 42

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

            insert_calls = mock_msg_repo.return_value.insert.call_args_list
            roles = [str(call.args[0].role) for call in insert_calls]
            contents = [call.args[0].content for call in insert_calls]
            assert "assistant" in roles
            assert "8000歩です。" in contents

    def test_chat_is_created_with_message_title(self):
        user = _make_mock_user()
        agent = _make_sse_stream("応答")

        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.UserRepository") as mock_user_repo, \
             patch("backend.controllers.chat.ChatRepository") as mock_chat_repo, \
             patch("backend.controllers.chat.MessageRepository"), \
             patch("backend.controllers.chat._agent", agent):

            mock_user_repo.return_value.find_by_fitbit_user_id.return_value = user
            mock_chat_repo.return_value.insert.return_value = 42

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

            inserted_chat = mock_chat_repo.return_value.insert.call_args.args[0]
            assert inserted_chat.user_id == user.id
            assert inserted_chat.title == "今日の歩数は？"
