import re
import urllib.parse
from datetime import datetime
from typing import Any

import httpx

from backend.schemas.auth import TokenResponse

BASE_URL = "https://api.fitbit.com/1/user/-"
AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"


class FitbitClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        redirect_uri: str = "http://localhost:8000/auth/fitbit/callback",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        params = urllib.parse.urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "scope": "activity heartrate weight nutrition",
                "redirect_uri": self._redirect_uri,
                "state": state,
            }
        )
        return f"{AUTH_URL}?{params}"

    def exchange_code_for_token(self, code: str) -> TokenResponse:
        response = httpx.post(
            url=TOKEN_URL,
            auth=(self._client_id, self._client_secret),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._redirect_uri,
            },
        )
        if response.status_code != 200:
            raise RuntimeError("トークンの交換に失敗しました")
        return TokenResponse(**response.json())

    def refresh_access_token(self) -> TokenResponse:
        response = httpx.post(
            url=TOKEN_URL,
            auth=(self._client_id, self._client_secret),
            data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
        )
        if response.status_code != 200:
            raise RuntimeError("トークンのリフレッシュに失敗しました")
        return TokenResponse(**response.json())

    def _get(
        self, endpoint: str, date: str | None = None, period: str | None = None
    ) -> dict[str, Any]:
        if date:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError(
                    f"日付のフォーマットが正しくありません。YYYY-MM-DD 形式で指定してください（例: 2026-05-20）。入力値: '{date}'"
                )
            resolved_date = date
        else:
            resolved_date = datetime.now().strftime("%Y-%m-%d")

        if period:
            url = f"{BASE_URL}/{endpoint}/{resolved_date}/{period}.json"
        else:
            url = f"{BASE_URL}/{endpoint}/{resolved_date}.json"

        response = httpx.get(url, headers={"Authorization": f"Bearer {self._access_token}"})

        if response.status_code == 200:
            result: dict[str, Any] = response.json()
            return result
        elif response.status_code == 401:
            raise RuntimeError("アクセストークンが無効です。再認証が必要です。(401)")
        elif response.status_code == 429:
            raise RuntimeError(
                "APIリクエスト上限に達しました。しばらく待ってから再試行してください。(429)"
            )
        elif response.status_code == 404:
            raise RuntimeError("指定期間のデータが見つかりません。(404)")
        else:
            raise RuntimeError(
                f"APIリクエストに失敗しました。({response.status_code}): {response.text}"
            )

    def get_activities(self, date: str | None = None) -> dict[str, Any]:
        return self._get("activities/date", date)

    def get_body_data(self, date: str | None = None) -> dict[str, Any]:
        return self._get("body/log/weight/date", date)

    def get_heart_rate(self, date: str | None = None, period: str = "1d") -> dict[str, Any]:
        return self._get("activities/heart/date", date, period)

    def get_food_log(self, date: str | None = None) -> dict[str, Any]:
        return self._get("foods/log/date", date)
