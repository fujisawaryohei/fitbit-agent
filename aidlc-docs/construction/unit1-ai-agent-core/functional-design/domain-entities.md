# Domain Entities — Unit 1: AI Agent Core

## エンティティ一覧

| エンティティ | 説明 | 関連ストーリー |
|---|---|---|
| AgentState | LangGraph グラフの状態（Pydantic） | US-09〜15 |
| FitbitData | Fitbit から取得した健康データ | US-04〜07 |
| WeightGoal | ユーザーの減量目標 | US-10 |
| CalorieDeficitResult | カロリー赤字計算の結果 | US-10 |
| CalorieBalance | カロリー収支サマリ | US-10 |
| WorkoutPlan | 自宅運動プラン | US-12 |
| WeeklyProgress | 週次進捗レポート | US-13 |
| MemoryEntry | Long-term memory の保存レコード | US-15 |
| TokenData | Fitbit アクセストークン | US-02 |

---

## AgentState

LangGraph グラフ全体で共有される状態。**Pydantic BaseModel** を使用する。

```python
from pydantic import BaseModel
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

    model_config = {"arbitrary_types_allowed": True}
```

**設計方針**: `messages` と `session_id` のみ保持。ユーザーの目標やキャッシュは持たない（BR-06-1）。

**Pydantic 採用理由**:
- 型バリデーションが自動で行われる
- フィールドのデフォルト値・バリデータを宣言的に定義できる
- 将来的なフィールド追加時にも型安全を保てる

---

## FitbitData

Fitbit API から取得した生データの統合表現。

```python
from pydantic import BaseModel

class FitbitData(BaseModel):
    date: str                          # "YYYY-MM-DD" または "today"
    steps: int | None = None           # 歩数
    calories_burned: int | None = None # 消費カロリー（kcal）
    weight_kg: float | None = None     # 体重（kg）
    bmi: float | None = None           # BMI
    heart_rate_avg: int | None = None  # 平均心拍数（bpm）
    calories_in: int | None = None     # 摂取カロリー（kcal）
```

**注**: 各フィールドは API レスポンスによって `None` になる場合がある。

---

## WeightGoal

ユーザーが指定した減量目標。会話の中で LLM が抽出する。

```python
from pydantic import BaseModel, field_validator

class WeightGoal(BaseModel):
    current_weight_kg: float
    target_weight_kg: float
    pace_kg_per_week: float = 0.5      # デフォルト: 0.5kg/週

    @field_validator("pace_kg_per_week")
    @classmethod
    def validate_pace(cls, v: float) -> float:
        if not (0.1 <= v <= 1.0):
            raise ValueError("pace_kg_per_week は 0.1〜1.0 の範囲で指定してください")
        return v

    @field_validator("target_weight_kg")
    @classmethod
    def validate_target(cls, v: float, info) -> float:
        current = info.data.get("current_weight_kg")
        if current is not None and v >= current:
            raise ValueError("target_weight_kg は current_weight_kg より軽くしてください")
        return v
```

---

## CalorieDeficitResult

`calculate_calorie_deficit` ツールの出力。

```python
from pydantic import BaseModel, field_validator

class CalorieDeficitResult(BaseModel):
    daily_deficit_kcal: int            # 1日の目標カロリー赤字
    weekly_deficit_kcal: int           # 週次カロリー赤字
    weeks_to_goal: float               # 目標達成までの週数
    days_to_goal: int                  # 目標達成までの日数
    total_loss_kg: float               # 総減量目標（kg）
    pace_kg_per_week: float            # 使用した週次ペース

    @field_validator("daily_deficit_kcal")
    @classmethod
    def validate_deficit(cls, v: int) -> int:
        if not (200 <= v <= 1000):
            raise ValueError("daily_deficit_kcal は 200〜1000 kcal の範囲内でなければなりません")
        return v
```

---

## CalorieBalance

1日のカロリー収支サマリ。

```python
from pydantic import BaseModel

class CalorieBalance(BaseModel):
    date: str
    calories_in: int                   # 摂取カロリー
    calories_burned: int               # 消費カロリー（Fitbit 計測）
    net_deficit: int                   # calories_burned - calories_in
```

---

## WorkoutPlan

LLM が生成する自宅運動プランの入出力。

```python
from pydantic import BaseModel
from typing import Literal

class WorkoutPlanInput(BaseModel):
    daily_deficit_kcal: int
    fitness_level: Literal["beginner", "intermediate", "advanced"]
    available_days_per_week: int       # 1〜7
    duration_minutes: int

class WorkoutPlan(BaseModel):
    fitness_level: Literal["beginner", "intermediate", "advanced"]
    available_days_per_week: int
    duration_minutes: int
    plan_text: str                     # LLM が生成したプラン全文（Markdown）
    estimated_calories_per_session: int | None = None
```

---

## WeeklyProgress

週次進捗の計算結果。

```python
from pydantic import BaseModel
from typing import Literal

class WeeklyProgress(BaseModel):
    current_weight_kg: float
    start_weight_kg: float
    actual_loss_kg: float
    expected_loss_kg: float
    progress_ratio: float              # actual / expected（1.0 = 目標通り）
    status: Literal["順調", "やや遅れ", "遅れ気味"]
    weeks_elapsed: int
```

---

## MemoryEntry

pgvector に保存される Long-term memory のレコード。

```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str                       # LLM が要約したテキスト
    embedding: list[float]             # ベクトル（pgvector に保存）
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}
```

**制約**: 同一 `session_id` のエントリは upsert（上書き更新）する。

---

## TokenData

Fitbit アクセストークンの保存形式。Unit 1 開発時は `.env` に手動設定。

```python
from pydantic import BaseModel
from datetime import datetime

class TokenData(BaseModel):
    session_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime               # トークン有効期限
    scope: str                         # 付与されたスコープ
```

---

## エンティティ関係図

```
AgentState (Pydantic BaseModel)
  ├─ messages: list[BaseMessage]
  │     └─ 会話履歴（WeightGoal は messages から LLM が参照）
  └─ session_id ──────────────────┐
                                  │
TokenData ──────────────── session_id
MemoryEntry ────────────── session_id

FitbitData ──────────────→ CalorieBalance（計算）
WeightGoal ──────────────→ CalorieDeficitResult（BLM-01）
WeightGoal + FitbitData ─→ WeeklyProgress（BLM-04）
CalorieDeficitResult ────→ WorkoutPlanInput（BLM-02）
WorkoutPlanInput ────────→ WorkoutPlan（LLM生成）
```

---

## ツールとエンティティのマッピング

| ツール（@tool） | 入力 | 出力エンティティ |
|---|---|---|
| `get_steps` | date, period | FitbitData.steps |
| `get_calories_burned` | date, period | FitbitData.calories_burned |
| `get_weight` | date, period | FitbitData.weight_kg, FitbitData.bmi |
| `get_heart_rate` | date, period | FitbitData.heart_rate_avg |
| `get_calories_in` | date | FitbitData.calories_in |
| `calculate_calorie_deficit` | WeightGoal | CalorieDeficitResult |
| `generate_home_workout_plan` | WorkoutPlanInput | WorkoutPlan.plan_text |
| `get_weekly_progress` | current/start weight, pace, weeks | WeeklyProgress |
