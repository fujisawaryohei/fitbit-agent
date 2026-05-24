from datetime import datetime, timedelta, timezone

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str
    user_id: str

    def expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=self.expires_in)


class AuthCallbackResponse(BaseModel):
    message: str = "Fitbit認証が完了しました"
    fitbit_user_id: str
    scope: str
