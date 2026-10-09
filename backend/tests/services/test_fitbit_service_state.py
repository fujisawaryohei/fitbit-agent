from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from backend.services.fitbit_service import (
    FitbitService,
    InvalidStateError,
    StateExpiredError,
)


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_authorization_url.return_value = "https://example.com/auth"
    return client


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_client, mock_repo):
    return FitbitService(mock_client, mock_repo)


class TestExpiredState:
    def test_expired_state_raises_and_is_removed(self, service, mock_client, mock_repo):
        _, state = service.get_authorization_url()
        service._state_store[state].created_at = datetime.now(timezone.utc) - timedelta(seconds=601)

        with pytest.raises(StateExpiredError):
            service.exchange_code_for_token("code", state)

        assert state not in service._state_store
        mock_client.exchange_code_for_token.assert_not_called()
        mock_repo.upsert.assert_not_called()

    def test_expired_state_cannot_be_retried(self, service):
        _, state = service.get_authorization_url()
        service._state_store[state].created_at = datetime.now(timezone.utc) - timedelta(seconds=601)
        with pytest.raises(StateExpiredError):
            service.exchange_code_for_token("code", state)

        # 削除済みなので 2 回目は「不正な state」になる
        with pytest.raises(InvalidStateError):
            service.exchange_code_for_token("code", state)

    def test_state_within_ttl_is_accepted(self, service, mock_client, mock_repo):
        _, state = service.get_authorization_url()
        service._state_store[state].created_at = datetime.now(timezone.utc) - timedelta(seconds=590)
        token = MagicMock(user_id="u", access_token="a", refresh_token="r", scope="s")
        mock_client.exchange_code_for_token.return_value = token

        user = service.exchange_code_for_token("code", state)

        assert user.fitbit_user_id == "u"
        mock_repo.upsert.assert_called_once_with(user)


class TestMissingCode:
    def test_none_code_raises_invalid_state_and_consumes_state(self, service, mock_client, mock_repo):
        _, state = service.get_authorization_url()

        with pytest.raises(InvalidStateError, match="code"):
            service.exchange_code_for_token(None, state)

        assert state not in service._state_store
        mock_client.exchange_code_for_token.assert_not_called()
        mock_repo.upsert.assert_not_called()
