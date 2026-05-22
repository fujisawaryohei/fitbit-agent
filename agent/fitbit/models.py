from datetime import datetime

from pydantic import BaseModel


class FitbitData(BaseModel):
    """Fitbit APIから取得したデータのオブジェクトマッピング"""

    date: str  # "YYYY-MM-DD" または "today"
    steps: int | None = None  # 歩数
    calories_burned: int | None = None  # 消費カロリー（kcal）
    weight_kg: float | None = None  # 体重（kg）
    bmi: float | None = None  # BMI
    heart_rate_avg: int | None = None  # 平均心拍数（bpm）
    calories_in: int | None = None  # 摂取カロリー（kcal）


class TokenData(BaseModel):
    """Fitbit API認証時のやり取りに利用するオブジェクト"""

    session_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str
