from datetime import datetime, timedelta, timezone

from backend.schemas.auth import TokenResponse


def _token(expires_in: int) -> TokenResponse:
    return TokenResponse(
        access_token="a",
        refresh_token="r",
        expires_in=expires_in,
        token_type="Bearer",
        scope="activity",
        user_id="ABC123",
    )


class TestExpiresAt:
    def test_is_now_plus_expires_in_seconds(self):
        before = datetime.now(timezone.utc)
        result = _token(28800).expires_at()
        after = datetime.now(timezone.utc)

        assert before + timedelta(seconds=28800) <= result <= after + timedelta(seconds=28800)

    def test_is_timezone_aware_utc(self):
        assert _token(60).expires_at().utcoffset() == timedelta(0)

    def test_zero_expires_in_is_now(self):
        before = datetime.now(timezone.utc)
        result = _token(0).expires_at()
        after = datetime.now(timezone.utc)

        assert before <= result <= after
