from datetime import datetime, timedelta, timezone


class User:
    def __init__(
        self,
        fitbit_user_id: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        scope: str,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.fitbit_user_id = fitbit_user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.scope = scope
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at

    def is_token_expired(self, buffer_minutes: int = 5) -> bool:
        return datetime.now(timezone.utc) >= self.token_expires_at - timedelta(minutes=buffer_minutes)
