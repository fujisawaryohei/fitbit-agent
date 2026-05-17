# Component Methods — Fitbit Weight Management AI Agent

> **Note**: このドキュメントはメソッドシグネチャと高レベルの目的を定義する。
> 詳細なビジネスロジック・バリデーション・エラーハンドリングは CONSTRUCTION フェーズの Functional Design で定義する。

---

## FastAPIApp

```python
# POST /chat — SSEストリーミングチャット
async def chat(request: ChatRequest) -> StreamingResponse:
    # Input:  ChatRequest(message: str, session_id: str)
    # Output: StreamingResponse (text/event-stream)
    # 処理:   AgentService に処理委譲し、SSEでチャンク送信

# GET /auth/fitbit — OAuth2認証開始
async def fitbit_auth() -> RedirectResponse:
    # Output: Fitbit認証URLへのリダイレクト

# GET /auth/fitbit/callback — OAuth2コールバック
async def fitbit_callback(code: str, state: str) -> JSONResponse:
    # Input:  code（認証コード）, state（CSRF対策トークン）
    # Output: 認証完了レスポンス

# GET /health
async def health() -> dict:
    # Output: {"status": "ok"}
```

---

## LangGraphAgent

```python
class LangGraphAgent:
    def build_graph(self) -> CompiledGraph:
        # グラフのノード・エッジを定義してコンパイル
        # Output: LangGraph CompiledGraph

    async def stream(self, message: str, session_id: str) -> AsyncIterator[str]:
        # AgentService Protocol の実装

    async def invoke(self, message: str, session_id: str) -> str:
        # AgentService Protocol の実装

# --- グラフノード関数 ---

def memory_inject_node(state: AgentState) -> AgentState:
    # Long-term memory を検索し、関連情報を SystemMessage としてコンテキストに注入
    # Input:  AgentState（messages, session_id）
    # Output: 更新された AgentState

def agent_node(state: AgentState) -> AgentState:
    # LLM を呼び出し、ツール使用判断または最終応答を生成
    # Input:  AgentState
    # Output: 更新された AgentState（tool_calls または final response）

def tool_node(state: AgentState) -> AgentState:
    # tool_calls に含まれるツールを実行し、結果を messages に追加
    # Input:  AgentState（tool_calls あり）
    # Output: 更新された AgentState（ToolMessage 追加済み）

def memory_save_node(state: AgentState) -> AgentState:
    # 会話から重要情報を抽出し Long-term memory に保存
    # Input:  AgentState
    # Output: AgentState（変更なし）

def should_continue(state: AgentState) -> str:
    # 条件分岐: tool_calls があれば "tool_node"、なければ "memory_save_node"
    # Output: 次ノード名（"tool_node" | "memory_save_node"）
```

---

## FitbitClient

```python
class FitbitClient:
    def get_authorization_url(self) -> str:
        # OAuth2認証URLを生成して返す
        # Output: Fitbit認証ページURL（+ state, code_challenge）

    def exchange_code_for_token(self, code: str, state: str) -> TokenData:
        # 認証コードをアクセストークンに交換
        # Input:  code（認証コード）、state（検証用）
        # Output: TokenData(access_token, refresh_token, expires_at)

    def refresh_access_token(self) -> TokenData:
        # リフレッシュトークンを使ってアクセストークンを更新
        # Output: 新しい TokenData

    def _get_valid_token(self) -> str:
        # 有効なアクセストークンを返す（期限切れなら自動リフレッシュ）
        # Output: access_token 文字列

    def get_activities(self, resource: str, date: str) -> dict:
        # 活動量データ（歩数・消費カロリー等）を取得する汎用メソッド
        # Input:  resource（"steps" | "calories" 等）、date（"today" | "YYYY-MM-DD"）
        # Output: Fitbit API レスポンス dict

    def get_body_data(self, resource: str, date: str) -> dict:
        # 体重・BMI データを取得する汎用メソッド
        # Input:  resource（"weight" | "bmi"）、date
        # Output: Fitbit API レスポンス dict

    def get_heart_rate(self, date: str) -> dict:
        # 心拍数データを取得
        # Input:  date
        # Output: Fitbit API レスポンス dict

    def get_food_log(self, date: str) -> dict:
        # 食事ログ（摂取カロリー）を取得
        # Input:  date
        # Output: Fitbit API レスポンス dict
```

---

## ToolRegistry（LangGraph @tool）

```python
@tool
def get_steps(date: str) -> dict:
    # 指定日の歩数を取得
    # Input:  date（"today" | "YYYY-MM-DD"）
    # Output: {"date": str, "steps": int}

@tool
def get_calories_burned(date: str) -> dict:
    # 指定日の消費カロリーを取得
    # Output: {"date": str, "calories_burned": float}

@tool
def get_weight(date: str) -> dict:
    # 直近の体重・BMI を取得
    # Output: {"date": str, "weight_kg": float, "bmi": float}

@tool
def get_heart_rate(date: str) -> dict:
    # 指定日の心拍数サマリーを取得
    # Output: {"date": str, "resting_heart_rate": int}

@tool
def get_calories_in(date: str) -> dict:
    # 指定日の摂取カロリー（食事ログ）を取得
    # Output: {"date": str, "calories_in": float, "logged": bool}

@tool
def calculate_calorie_deficit(
    current_weight_kg: float,
    target_weight_kg: float,
    weeks: int
) -> dict:
    # 目標達成に必要な1日あたりのカロリー赤字・推奨摂取カロリーを計算
    # Output: {"daily_deficit": float, "daily_intake_target": float, "weekly_loss_kg": float}

@tool
def generate_home_workout_plan(
    calorie_target_per_day: float,
    fitness_level: str  # "beginner" | "intermediate" | "advanced"
) -> dict:
    # 自宅運動プランを生成（種目・回数・フォーム説明・初心者バリエーション含む）
    # Output: {"plan": list[ExerciseItem], "weekly_schedule": dict}

@tool
def get_weekly_progress(start_date: str, end_date: str) -> dict:
    # 週次進捗サマリーを集計（複数Fitbitツールを内部で呼び出し）
    # Output: {"avg_steps": float, "total_calories_burned": float, "weight_change_kg": float}
```

---

## MemoryManager

```python
class MemoryManager:
    def search_long_term(self, query: str, k: int = 5) -> list[Document]:
        # Long-term memory からセマンティック検索
        # Input:  query（検索クエリ）、k（取得件数）
        # Output: 関連ドキュメントリスト

    def save_long_term(self, content: str, metadata: dict) -> None:
        # 重要情報をエンベディングして pgvector に保存
        # Input:  content（保存テキスト）、metadata（タグ・タイムスタンプ等）

    def update_long_term(self, query: str, new_content: str, metadata: dict) -> None:
        # 既存の関連エントリを削除して新しい情報で上書き
        # Input:  query（更新対象の検索クエリ）、new_content、metadata

    def format_context_for_injection(self, documents: list[Document]) -> str:
        # 検索結果を System Message に注入するテキスト形式に変換
        # Output: フォーマット済みコンテキスト文字列
```
