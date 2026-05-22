import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.fitbit.com/1/user/-"


class FitbitClient:
    def _get_valid_token(self) -> str:
        access_token = os.getenv("FITBIT_ACCESS_TOKEN", "")
        expires_at_str = os.getenv("FITBIT_EXPIRES_AT", "")

        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5):
                return self._refresh_token()

        if not access_token:
            raise RuntimeError("FITBIT_ACCESS_TOKEN が設定されていません。")
        return access_token

    def _refresh_token(self) -> str:
        refresh_token = os.getenv("FITBIT_REFRESH_TOKEN", "")
        client_id = os.getenv("FITBIT_CLIENT_ID", "")
        client_secret = os.getenv("FITBIT_CLIENT_SECRET", "")

        response = httpx.post(
            "https://api.fitbit.com/oauth2/token",
            auth=(client_id, client_secret),
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        if response.status_code != 200:
            raise RuntimeError(f"トークンリフレッシュに失敗しました。({response.status_code})")

        tokens = response.json()
        os.environ["FITBIT_ACCESS_TOKEN"] = tokens.get("access_token", "")
        if "refresh_token" in tokens:
            os.environ["FITBIT_REFRESH_TOKEN"] = tokens["refresh_token"]

        return str(tokens.get("access_token", ""))

    def _get(self, endpoint: str, date: str | None = None, period: str | None = None) -> dict[str, Any]:
        token = self._get_valid_token()

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

        response = httpx.get(url, headers={"Authorization": f"Bearer {token}"})

        if response.status_code == 200:
            result: dict[str, Any] = response.json()
            return result
        elif response.status_code == 401:
            raise RuntimeError("アクセストークンが無効です。再認証が必要です。(401)")
        elif response.status_code == 429:
            raise RuntimeError("APIリクエスト上限に達しました。しばらく待ってから再試行してください。(429)")
        elif response.status_code == 404:
            raise RuntimeError("指定期間のデータが見つかりません。(404)")
        else:
            raise RuntimeError(f"APIリクエストに失敗しました。({response.status_code}): {response.text}")

    def get_activities(self, date: str | None = None) -> dict[str, Any]:
        return self._get("activities/date", date)

    def get_body_data(self, date: str | None = None) -> dict[str, Any]:
        return self._get("body/log/weight/date", date)

    def get_heart_rate(self, date: str | None = None, period: str = "1d") -> dict[str, Any]:
        return self._get("activities/heart/date", date, period)

    def get_food_log(self, date: str | None = None) -> dict[str, Any]:
        return self._get("foods/log/date", date)
