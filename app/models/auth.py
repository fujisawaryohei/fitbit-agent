import secrets
from datetime import datetime, timedelta, timezone


class CsrfState:
    def __init__(self, value: str, created_at: datetime) -> None:
        self.value = value
        self.created_at = created_at

    @classmethod
    def generate(cls) -> "CsrfState":
        return cls(value=secrets.token_urlsafe(), created_at=datetime.now(timezone.utc))

    def is_expired(self, ttl_seconds: int = 600) -> bool:
        return datetime.now(timezone.utc) > self.created_at + timedelta(seconds=ttl_seconds)
