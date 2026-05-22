from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from agent.fitbit.client import FitbitClient


@pytest.fixture
def client() -> FitbitClient:
    return FitbitClient()


@pytest.fixture
def valid_token_env(monkeypatch: pytest.MonkeyPatch) -> None:
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    monkeypatch.setenv("FITBIT_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("FITBIT_EXPIRES_AT", future)


class TestGetValidToken:
    def test_returns_token_when_valid(self, client: FitbitClient, valid_token_env: None) -> None:
        assert client._get_valid_token() == "test-token"

    def test_raises_when_no_token(self, client: FitbitClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FITBIT_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FITBIT_EXPIRES_AT", raising=False)
        with pytest.raises(RuntimeError, match="FITBIT_ACCESS_TOKEN"):
            client._get_valid_token()

    def test_refreshes_when_expired(self, client: FitbitClient, monkeypatch: pytest.MonkeyPatch) -> None:
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        monkeypatch.setenv("FITBIT_ACCESS_TOKEN", "old-token")
        monkeypatch.setenv("FITBIT_EXPIRES_AT", past)
        with patch.object(client, "_refresh_token", return_value="new-token") as mock_refresh:
            result = client._get_valid_token()
        mock_refresh.assert_called_once()
        assert result == "new-token"


class TestGet:
    def _mock_response(self, status_code: int, json_data: dict | None = None, text: str = "") -> MagicMock:
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        mock.text = text
        return mock

    def test_get_activities_success(self, client: FitbitClient, valid_token_env: None) -> None:
        expected = {"summary": {"steps": 8000}}
        with patch("httpx.get", return_value=self._mock_response(200, expected)):
            result = client.get_activities("2026-05-20")
        assert result == expected

    def test_get_with_invalid_date_format(self, client: FitbitClient, valid_token_env: None) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            client.get_activities("2026-5-1")

    def test_get_401_raises(self, client: FitbitClient, valid_token_env: None) -> None:
        with patch("httpx.get", return_value=self._mock_response(401)):
            with pytest.raises(RuntimeError, match="401"):
                client.get_activities("2026-05-20")

    def test_get_429_raises(self, client: FitbitClient, valid_token_env: None) -> None:
        with patch("httpx.get", return_value=self._mock_response(429)):
            with pytest.raises(RuntimeError, match="429"):
                client.get_activities("2026-05-20")

    def test_get_404_raises(self, client: FitbitClient, valid_token_env: None) -> None:
        with patch("httpx.get", return_value=self._mock_response(404)):
            with pytest.raises(RuntimeError, match="404"):
                client.get_activities("2026-05-20")

    def test_get_500_raises(self, client: FitbitClient, valid_token_env: None) -> None:
        with patch("httpx.get", return_value=self._mock_response(500, text="Internal Server Error")):
            with pytest.raises(RuntimeError, match="500"):
                client.get_activities("2026-05-20")

    def test_get_without_date_uses_today(self, client: FitbitClient, valid_token_env: None) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        with patch("httpx.get", return_value=self._mock_response(200, {})) as mock_get:
            client.get_activities()
        url = mock_get.call_args[0][0]
        assert today in url

    def test_get_heart_rate_with_period(self, client: FitbitClient, valid_token_env: None) -> None:
        with patch("httpx.get", return_value=self._mock_response(200, {})) as mock_get:
            client.get_heart_rate("2026-05-20", period="1d")
        url = mock_get.call_args[0][0]
        assert "1d" in url
