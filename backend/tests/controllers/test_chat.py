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
    user.is_token_expired.return_value = expired
    user.access_token = "access-token"
    user.refresh_token = "refresh-token"
    return user


class TestChatAuth:
    def test_no_cookie_returns_401(self):
        client = TestClient(_app)
        response = client.post("/chat", json={"message": "こんにちは", "session_id": "test-001"})
        assert response.status_code == 401
        assert "認証が必要です" in response.json()["detail"]

    def test_unknown_user_returns_401(self):
        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.UserRepository") as mock_repo_class:
            mock_repo_class.return_value.find_by_fitbit_user_id.return_value = None
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "unknown-user")
            response = client.post("/chat", json={"message": "こんにちは", "session_id": "test-001"})
        assert response.status_code == 401
        assert "ユーザーが見つかりません" in response.json()["detail"]

    def test_expired_token_returns_401(self):
        with patch("backend.controllers.chat.get_connection", return_value=MagicMock()), \
             patch("backend.controllers.chat.UserRepository") as mock_repo_class:
            mock_repo_class.return_value.find_by_fitbit_user_id.return_value = _make_mock_user(expired=True)
            client = TestClient(_app)
            client.cookies.set("fitbit_user_id", "ABC123")
            response = client.post("/chat", json={"message": "こんにちは", "session_id": "test-001"})
        assert response.status_code == 401
        assert "有効期限" in response.json()["detail"]
