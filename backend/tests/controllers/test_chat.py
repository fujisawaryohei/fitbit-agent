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


class TestGetChats:
    def _make_chats(self):
        from datetime import datetime

        from backend.models.chat import Chat

        return [
            Chat(
                id=1,
                user_id=1,
                title="今日の歩数は？",
                created_at=datetime(2026, 5, 29, 10, 0, 0),
            ),
            Chat(
                id=2,
                user_id=1,
                title="睡眠時間は？",
                created_at=datetime(2026, 5, 29, 11, 0, 0),
            ),
        ]

    def test_no_cookie_returns_401(self):
        client = TestClient(_app)
        response = client.get("/chats")
        assert response.status_code == 401
        assert "認証が必要です" in response.json()["detail"]

    def test_unknown_user_returns_401(self, container):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = None

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(MagicMock()):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "unknown-user")
            response = client.get("/chats")

        assert response.status_code == 401
        assert "ユーザーが見つかりません" in response.json()["detail"]

    def test_returns_chat_summaries(self, container):
        user = _make_mock_user()
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = user
        mock_chat_repo = MagicMock()
        mock_chat_repo.list.return_value = self._make_chats()

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.get("/chats")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["id"] == 1
        assert body[0]["title"] == "今日の歩数は？"
        assert "created_at" in body[0]
        assert body[1]["id"] == 2
        assert body[1]["title"] == "睡眠時間は？"
        mock_chat_repo.list.assert_called_once_with(user.id)


class TestGetMessages:
    def _make_chat(self, chat_id=42, user_id=1):
        from backend.models.chat import Chat

        return Chat(id=chat_id, user_id=user_id, title="今日の歩数は？")

    def _make_messages(self, chat_id=42):
        from datetime import datetime

        from backend.models.message import Message
        from backend.models.message_role import MessageRole

        return [
            Message(
                id=1,
                chat_id=chat_id,
                role=MessageRole.USER,
                content="今日の歩数は？",
                created_at=datetime(2026, 5, 29, 10, 0, 0),
            ),
            Message(
                id=2,
                chat_id=chat_id,
                role=MessageRole.ASSISTANT,
                content="8000歩です。",
                created_at=datetime(2026, 5, 29, 10, 0, 1),
            ),
        ]

    def test_no_cookie_returns_401(self):
        client = TestClient(_app)
        response = client.get("/chats/42/messages")
        assert response.status_code == 401
        assert "認証が必要です" in response.json()["detail"]

    def test_returns_messages(self, container):
        user = _make_mock_user()
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = user
        mock_chat_repo = MagicMock()
        mock_chat_repo.find_by_id.return_value = self._make_chat()
        mock_msg_repo = MagicMock()
        mock_msg_repo.list.return_value = self._make_messages()

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             container.message_repo.override(mock_msg_repo):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.get("/chats/42/messages")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["role"] == "user"
        assert body[0]["content"] == "今日の歩数は？"
        assert body[1]["role"] == "assistant"
        assert body[1]["content"] == "8000歩です。"
        mock_msg_repo.list.assert_called_once_with(42)

    def test_unknown_user_returns_401(self, container):
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = None

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(MagicMock()), \
             container.message_repo.override(MagicMock()):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "unknown-user")
            response = client.get("/chats/42/messages")

        assert response.status_code == 401
        assert "ユーザーが見つかりません" in response.json()["detail"]

    def test_other_users_chat_returns_404(self, container):
        user = _make_mock_user()
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = user
        mock_chat_repo = MagicMock()
        mock_chat_repo.find_by_id.return_value = self._make_chat(user_id=999)
        mock_msg_repo = MagicMock()

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             container.message_repo.override(mock_msg_repo):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.get("/chats/42/messages")

        assert response.status_code == 404
        assert "チャットが見つかりません" in response.json()["detail"]
        mock_msg_repo.list.assert_not_called()

    def test_missing_chat_returns_404(self, container):
        user = _make_mock_user()
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_fitbit_user_id.return_value = user
        mock_chat_repo = MagicMock()
        mock_chat_repo.find_by_id.return_value = None
        mock_msg_repo = MagicMock()

        with container.user_repo.override(mock_user_repo), \
             container.chat_repo.override(mock_chat_repo), \
             container.message_repo.override(mock_msg_repo):
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.get("/chats/42/messages")

        assert response.status_code == 404
        mock_msg_repo.list.assert_not_called()
