from typing import Literal

from pydantic import BaseModel, ValidationInfo, field_validator


class WeightGoal(BaseModel):
    """ユーザーが指定した減量目標。会話の中で LLM が抽出する。"""

    current_weight_kg: float
    target_weight_kg: float
    pace_kg_per_week: float = 0.5  # デフォルト 0.5kg/週

    @field_validator("pace_kg_per_week")
    @classmethod
    def validate_pace(cls, value: float) -> float:
        if not (0.1 <= value <= 1.0):
            raise ValueError("pace_kg_per_weekは、0.1〜1.0の範囲で指定してください。")
        return value

    @field_validator("target_weight_kg")
    @classmethod
    def validate_target(cls, value: float, info: ValidationInfo) -> float:
        current = info.data.get("current_weight_kg")

        if current is not None and value >= current:
            raise ValueError("target_weight_kg は current_weight_kg より軽くしてください。")
        return value


class CalorieDeficitResult(BaseModel):
    """`calculate_calorie_deficit` ツールの出力。"""

    daily_deficit_kcal: int  # 1日の目標カロリー赤字
    weekly_deficit_kcal: int  # 週次カロリー赤字
    weeks_to_goal: float  # 目標達成までの週数
    days_to_goal: int  # 目標達成までの日数
    total_loss_kg: float  # 総減量目標（kg）
    pace_kg_per_week: float  # 使用した週次ペース

    @field_validator("daily_deficit_kcal")
    @classmethod
    def validate_deficit(cls, v: int) -> int:
        if not (200 <= v <= 1000):
            raise ValueError("daily_deficit_kcal は 200〜1000 kcal の範囲内でなければなりません")
        return v


class CalorieBalance(BaseModel):
    """1日のカロリー収支サマリ。"""

    date: str
    calories_in: int  # 摂取カロリー
    calories_burned: int  # 消費カロリー（Fitbit 計測）
    net_deficit: int  # calories_burned - calories_in


class WorkoutPlanInput(BaseModel):
    """LLMが生成する自宅運動プランの入力用"""

    daily_deficit_kcal: int
    fitness_level: Literal["beginner", "intermediate", "advanced"]
    available_days_per_week: int  # 1〜7
    duration_minutes: int


class WorkoutPlan(BaseModel):
    """LLMが生成する自宅運動プランの出力用"""

    fitness_level: Literal["beginner", "intermediate", "advanced"]
    available_days_per_week: int
    duration_minutes: int
    plan_text: str  # LLM が生成したプラン全文（Markdown）
    estimated_calories_per_session: int | None = None


class WeeklyProgress(BaseModel):
    """週次進捗の計算結果"""

    current_weight_kg: float
    start_weight_kg: float
    actual_loss_kg: float
    expected_loss_kg: float
    progress_ratio: float  # actual / expected（1.0 = 目標通り）
    status: Literal["順調", "やや遅れ", "遅れ気味"]
    weeks_elapsed: int
