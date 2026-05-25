from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.services.fitbit_service import FitbitService


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_client, mock_repo):
    return FitbitService(mock_client, mock_repo)


def make_token_response(mock_client):
    expires_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token = MagicMock()
    token.user_id = "fitbit-user-123"
    token.access_token = "access-abc"
    token.refresh_token = "refresh-xyz"
    token.scope = "activity heartrate"
    token.expires_at.return_value = expires_at
    return token


class TestGetAuthorizationUrl:
    def test_returns_url_and_state(self, mock_client, service):
        mock_client.get_authorization_url.return_value = "https://example.com/auth"
        url, state = service.get_authorization_url()
        assert url == "https://example.com/auth"
        assert isinstance(state, str)
        assert len(state) > 0

    def test_passes_generated_state_to_client(self, mock_client, service):
        mock_client.get_authorization_url.return_value = "https://example.com/auth"
        _, state = service.get_authorization_url()
        mock_client.get_authorization_url.assert_called_once_with(state)

    def test_state_is_stored_in_state_store(self, mock_client, service):
        mock_client.get_authorization_url.return_value = "https://example.com/auth"
        _, state = service.get_authorization_url()
        assert state in service._state_store


class TestExchangeCodeForToken:
    def test_calls_client_exchange(self, mock_client, mock_repo, service):
        mock_client.exchange_code_for_token.return_value = make_token_response(mock_client)
        service.exchange_code_for_token("auth-code-123")
        mock_client.exchange_code_for_token.assert_called_once_with("auth-code-123")

    def test_upserts_user_to_repository(self, mock_client, mock_repo, service):
        mock_client.exchange_code_for_token.return_value = make_token_response(mock_client)
        service.exchange_code_for_token("auth-code-123")
        mock_repo.upsert.assert_called_once()
        user = mock_repo.upsert.call_args[0][0]
        assert user.fitbit_user_id == "fitbit-user-123"
        assert user.access_token == "access-abc"
        assert user.refresh_token == "refresh-xyz"
        assert user.scope == "activity heartrate"


class TestUpdateToken:
    def test_calls_client_refresh(self, mock_client, mock_repo, service):
        mock_client.refresh_access_token.return_value = make_token_response(mock_client)
        service.update_token()
        mock_client.refresh_access_token.assert_called_once()

    def test_updates_tokens_in_repository(self, mock_client, mock_repo, service):
        mock_client.refresh_access_token.return_value = make_token_response(mock_client)
        service.update_token()
        mock_repo.update_tokens.assert_called_once_with(
            fitbit_user_id="fitbit-user-123",
            access_token="access-abc",
            refresh_token="refresh-xyz",
            token_expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
