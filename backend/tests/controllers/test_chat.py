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
    from langchain_core.messages import AIMessage

    async def _gen():
        for chunk in chunks:
            yield AIMessage(content=chunk), {"langgraph_node": "agent_node"}

    mock = MagicMock()
    mock.astream.return_value = _gen()
    return mock


class TestChatAuth:
    def test_no_cookie_returns_401(self):
        client = TestClient(_app)
        response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "認証が必要です" in response.json()["detail"]

    def test_unknown_user_returns_401(self, container):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = None
        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(MagicMock()):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "unknown-user")
            response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "ユーザーが見つかりません" in response.json()["detail"]

    def test_expired_token_returns_401(self, container):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = _make_mock_user(expired=True)
        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(MagicMock()):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.post("/chat", json={"message": "こんにちは"})
        assert response.status_code == 401
        assert "有効期限" in response.json()["detail"]


class TestChatStreaming:
    def _setup(self, user, chat_id=42):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = user
        mock_chat_repo = MagicMock()
        mock_chat_repo.insert.return_value = chat_id
        mock_msg_repo = MagicMock()
        return mock_user_repo, mock_chat_repo, mock_msg_repo

    def test_sse_chunks_and_done_are_returned(self, container):
        user = _make_mock_user()
        agent = _make_sse_stream("今日", "の歩数は")
        mock_user_repo, mock_chat_repo, mock_msg_repo = self._setup(user)

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.MessageRepository", return_value=mock_msg_repo), \
             patch("backend.controllers.chat._agent", agent):

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

    def test_user_message_is_saved_to_db(self, container):
        user = _make_mock_user()
        agent = _make_sse_stream("応答")
        mock_user_repo, mock_chat_repo, mock_msg_repo = self._setup(user)

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.MessageRepository", return_value=mock_msg_repo), \
             patch("backend.controllers.chat._agent", agent):

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

        roles = [str(call.args[0].role) for call in mock_msg_repo.insert.call_args_list]
        assert "user" in roles

    def test_assistant_message_is_saved_to_db(self, container):
        user = _make_mock_user()
        agent = _make_sse_stream("8000歩です。")
        mock_user_repo, mock_chat_repo, mock_msg_repo = self._setup(user)

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.MessageRepository", return_value=mock_msg_repo), \
             patch("backend.controllers.chat._agent", agent):

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

        roles = [str(call.args[0].role) for call in mock_msg_repo.insert.call_args_list]
        contents = [call.args[0].content for call in mock_msg_repo.insert.call_args_list]
        assert "assistant" in roles
        assert "8000歩です。" in contents

    def test_chat_is_created_with_message_title(self, container):
        user = _make_mock_user()
        agent = _make_sse_stream("応答")
        mock_user_repo, mock_chat_repo, mock_msg_repo = self._setup(user)

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.release_connection"), \
             patch("backend.controllers.chat.MessageRepository", return_value=mock_msg_repo), \
             patch("backend.controllers.chat._agent", agent):

            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            with client.stream("POST", "/chat", json={"message": "今日の歩数は？"}):
                pass

        inserted_chat = mock_chat_repo.insert.call_args.args[0]
        assert inserted_chat.user_id == user.id
        assert inserted_chat.title == "今日の歩数は？"
