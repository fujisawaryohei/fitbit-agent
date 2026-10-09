from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.controllers.auth import router as auth_router

_app = FastAPI()
_app.include_router(auth_router)


class TestAuthorizationUrlFailure:
    def test_returns_500_when_url_is_none(self, container):
        mock_service = MagicMock()
        mock_service.get_authorization_url.return_value = (None, "state")
        with container.fitbit_service.override(mock_service):
            client = TestClient(_app, follow_redirects=False)
            response = client.get("/auth/fitbit")
        assert response.status_code == 500
        assert response.json()["detail"] == "URLの発行に失敗しました"
