from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from backend.models.user import User

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _user(expires_at: datetime) -> User:
    return User(
        fitbit_user_id="ABC123",
        access_token="a",
        refresh_token="r",
        token_expires_at=expires_at,
        scope="activity",
    )


def _is_expired(user: User, **kwargs) -> bool:
    with patch("backend.models.user.datetime") as mock_dt:
        mock_dt.now.return_value = NOW
        return user.is_token_expired(**kwargs)


class TestIsTokenExpired:
    def test_far_future_is_not_expired(self):
        assert _is_expired(_user(NOW + timedelta(hours=8))) is False

    def test_one_second_before_buffer_start_is_not_expired(self):
        # 期限の 5 分前 = NOW + 5 分。それより 1 秒先ならまだ有効
        assert _is_expired(_user(NOW + timedelta(minutes=5, seconds=1))) is False

    def test_exactly_at_buffer_start_is_expired(self):
        assert _is_expired(_user(NOW + timedelta(minutes=5))) is True

    def test_inside_buffer_is_expired(self):
        assert _is_expired(_user(NOW + timedelta(minutes=4, seconds=59))) is True

    def test_past_expiry_is_expired(self):
        assert _is_expired(_user(NOW - timedelta(seconds=1))) is True

    def test_custom_buffer_minutes(self):
        user = _user(NOW + timedelta(minutes=10))
        assert _is_expired(user, buffer_minutes=5) is False
        assert _is_expired(user, buffer_minutes=10) is True

    def test_zero_buffer_expires_exactly_at_expiry(self):
        assert _is_expired(_user(NOW), buffer_minutes=0) is True
        assert _is_expired(_user(NOW + timedelta(seconds=1)), buffer_minutes=0) is False
