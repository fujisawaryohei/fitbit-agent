from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers.auth import router as auth_router
from app.services.fitbit_service import InvalidStateError, StateExpiredError

_app = FastAPI()
_app.include_router(auth_router)


def _make_mock_service(
    auth_url: str = "https://www.fitbit.com/oauth2/authorize?client_id=test",
    state: str = "test-state",
) -> MagicMock:
    mock = MagicMock()
    mock.get_authorization_url.return_value = (auth_url, state)
    return mock


def _make_mock_user(fitbit_user_id: str = "ABC123", scope: str = "activity heartrate") -> MagicMock:
    user = MagicMock()
    user.fitbit_user_id = fitbit_user_id
    user.scope = scope
    return user


class TestAuthorizationUrl:
    def test_redirects_to_fitbit(self):
        mock_service = _make_mock_service()
        with patch("app.controllers.auth._get_service", return_value=mock_service):
            client = TestClient(_app, follow_redirects=False)
            response = client.get("/auth/fitbit")
        assert response.status_code in (302, 307)
        assert "fitbit.com" in response.headers["location"]


class TestCallback:
    def test_redirects_to_frontend(self):
        mock_service = _make_mock_service()
        mock_service.exchange_code_for_token.return_value = _make_mock_user()
        with patch("app.controllers.auth._get_service", return_value=mock_service):
            client = TestClient(_app, follow_redirects=False)
            response = client.get(
                "/auth/fitbit/callback", params={"code": "auth-code", "state": "test-state"}
            )
        assert response.status_code == 302
        assert response.cookies.get("fitbit_user_id") == "ABC123"
        assert response.cookies.get("fitbit_connected") == "true"

    def test_invalid_state_returns_400(self):
        mock_service = _make_mock_service()
        mock_service.exchange_code_for_token.side_effect = InvalidStateError()
        with patch("app.controllers.auth._get_service", return_value=mock_service):
            client = TestClient(_app)
            response = client.get(
                "/auth/fitbit/callback", params={"code": "auth-code", "state": "bad-state"}
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "不正なリクエストです"

    def test_expired_state_returns_400(self):
        mock_service = _make_mock_service()
        mock_service.exchange_code_for_token.side_effect = StateExpiredError()
        with patch("app.controllers.auth._get_service", return_value=mock_service):
            client = TestClient(_app)
            response = client.get(
                "/auth/fitbit/callback", params={"code": "auth-code", "state": "expired-state"}
            )
        assert response.status_code == 400
        assert "タイムアウト" in response.json()["detail"]
