import urllib.parse
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from agent.fitbit.client import AUTH_URL, BASE_URL, TOKEN_URL, FitbitClient


@pytest.fixture
def client() -> FitbitClient:
    return FitbitClient(
        client_id="test-client-id",
        client_secret="test-client-secret",
        access_token="test-token",
        refresh_token="test-refresh-token",
    )


class TestGet:
    def _mock_response(self, status_code: int, json_data: dict | None = None, text: str = "") -> MagicMock:
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data or {}
        mock.text = text
        return mock

    def test_get_activities_success(self, client: FitbitClient) -> None:
        expected = {"summary": {"steps": 8000}}
        with patch("httpx.get", return_value=self._mock_response(200, expected)):
            result = client.get_activities("2026-05-20")
        assert result == expected

    def test_get_with_invalid_date_format(self, client: FitbitClient) -> None:
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            client.get_activities("2026-5-1")

    def test_get_401_raises(self, client: FitbitClient) -> None:
        with patch("httpx.get", return_value=self._mock_response(401)):
            with pytest.raises(RuntimeError, match="401"):
                client.get_activities("2026-05-20")

    def test_get_429_raises(self, client: FitbitClient) -> None:
        with patch("httpx.get", return_value=self._mock_response(429)):
            with pytest.raises(RuntimeError, match="429"):
                client.get_activities("2026-05-20")

    def test_get_404_raises(self, client: FitbitClient) -> None:
        with patch("httpx.get", return_value=self._mock_response(404)):
            with pytest.raises(RuntimeError, match="404"):
                client.get_activities("2026-05-20")

    def test_get_500_raises(self, client: FitbitClient) -> None:
        with patch("httpx.get", return_value=self._mock_response(500, text="Internal Server Error")):
            with pytest.raises(RuntimeError, match="500"):
                client.get_activities("2026-05-20")

    def test_get_without_date_uses_today(self, client: FitbitClient) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        with patch("httpx.get", return_value=self._mock_response(200, {})) as mock_get:
            client.get_activities()
        url = mock_get.call_args[0][0]
        assert today in url

    def test_get_heart_rate_with_period(self, client: FitbitClient) -> None:
        with patch("httpx.get", return_value=self._mock_response(200, {})) as mock_get:
            client.get_heart_rate("2026-05-20", period="1d")
        url = mock_get.call_args[0][0]
        assert "1d" in url


TOKEN_JSON = {
    "access_token": "new-access",
    "refresh_token": "new-refresh",
    "expires_in": 28800,
    "token_type": "Bearer",
    "scope": "activity heartrate weight nutrition",
    "user_id": "ABC123",
}


def _token_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data if json_data is not None else {}
    return mock


class TestAuthorizationUrl:
    def test_query_contains_oauth_params(self, client: FitbitClient) -> None:
        url = client.get_authorization_url("state-123")
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)

        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == AUTH_URL
        assert query["client_id"] == ["test-client-id"]
        assert query["response_type"] == ["code"]
        assert query["scope"] == ["activity heartrate weight nutrition"]
        assert query["redirect_uri"] == ["http://localhost:8000/auth/fitbit/callback"]
        assert query["state"] == ["state-123"]

    def test_custom_redirect_uri_is_used(self) -> None:
        custom = FitbitClient("id", "secret", redirect_uri="https://example.com/cb")
        query = urllib.parse.parse_qs(urllib.parse.urlparse(custom.get_authorization_url("s")).query)
        assert query["redirect_uri"] == ["https://example.com/cb"]


class TestExchangeCodeForToken:
    def test_success_posts_form_with_basic_auth(self, client: FitbitClient) -> None:
        with patch("httpx.post", return_value=_token_response(200, TOKEN_JSON)) as mock_post:
            token = client.exchange_code_for_token("auth-code")

        kwargs = mock_post.call_args.kwargs
        assert kwargs["url"] == TOKEN_URL
        assert kwargs["auth"] == ("test-client-id", "test-client-secret")
        assert kwargs["data"] == {
            "grant_type": "authorization_code",
            "code": "auth-code",
            "redirect_uri": "http://localhost:8000/auth/fitbit/callback",
        }
        assert token.access_token == "new-access"
        assert token.refresh_token == "new-refresh"
        assert token.user_id == "ABC123"

    def test_non_200_raises(self, client: FitbitClient) -> None:
        with patch("httpx.post", return_value=_token_response(400)):
            with pytest.raises(RuntimeError, match="トークンの交換"):
                client.exchange_code_for_token("bad-code")


class TestRefreshAccessToken:
    def test_success_posts_refresh_grant_with_basic_auth(self, client: FitbitClient) -> None:
        with patch("httpx.post", return_value=_token_response(200, TOKEN_JSON)) as mock_post:
            token = client.refresh_access_token()

        kwargs = mock_post.call_args.kwargs
        assert kwargs["url"] == TOKEN_URL
        assert kwargs["auth"] == ("test-client-id", "test-client-secret")
        assert kwargs["data"] == {
            "grant_type": "refresh_token",
            "refresh_token": "test-refresh-token",
        }
        assert token.access_token == "new-access"

    def test_non_200_raises(self, client: FitbitClient) -> None:
        with patch("httpx.post", return_value=_token_response(401)):
            with pytest.raises(RuntimeError, match="リフレッシュ"):
                client.refresh_access_token()


class TestDataEndpoints:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("get_body_data", "body/log/weight/date/2026-05-20.json"),
            ("get_food_log", "foods/log/date/2026-05-20.json"),
        ],
    )
    def test_url_and_bearer_header(self, client: FitbitClient, method: str, path: str) -> None:
        with patch("httpx.get", return_value=_token_response(200, {"ok": True})) as mock_get:
            result = getattr(client, method)("2026-05-20")

        assert mock_get.call_args[0][0] == f"{BASE_URL}/{path}"
        assert mock_get.call_args.kwargs["headers"] == {"Authorization": "Bearer test-token"}
        assert result == {"ok": True}
