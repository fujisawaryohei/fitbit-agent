# Code Generation Plan — Unit 1: AI Agent Core

> **注**: コード生成はユーザーが自己実装。このドキュメントは実装タスクリストとして使用する。

## 対象ストーリー
US-02, US-04〜07, US-09〜15

## 設計アーティファクト参照先
| 種別 | ファイル |
|---|---|
| ビジネスロジック | `aidlc-docs/construction/unit1-ai-agent-core/functional-design/business-logic-model.md` |
| ドメインエンティティ | `aidlc-docs/construction/unit1-ai-agent-core/functional-design/domain-entities.md` |
| ビジネスルール | `aidlc-docs/construction/unit1-ai-agent-core/functional-design/business-rules.md` |
| NFR要件 | `aidlc-docs/construction/unit1-ai-agent-core/nfr-requirements/nfr-requirements.md` |
| 技術スタック | `aidlc-docs/construction/unit1-ai-agent-core/nfr-requirements/tech-stack-decisions.md` |
| NFRパターン | `aidlc-docs/construction/unit1-ai-agent-core/nfr-design/nfr-design-patterns.md` |
| 論理コンポーネント | `aidlc-docs/construction/unit1-ai-agent-core/nfr-design/logical-components.md` |

---

## Phase 1: プロジェクトセットアップ

### Step 1: pyproject.toml の作成
- [x] `pyproject.toml` を workspace root に作成
- [x] `requires-python = ">=3.11"` を設定
- [x] 依存ライブラリを定義（`tech-stack-decisions.md` の依存ライブラリ一覧を参照）
  - langgraph, langchain-core, langchain-anthropic, langfuse
  - sentence-transformers, psycopg2-binary, pgvector
  - python-dotenv, httpx, pydantic
- [x] dev 依存: pytest, hypothesis, mypy, ruff

### Step 2: 環境設定ファイルの作成
- [x] `.env.example` を作成（`logical-components.md` の環境変数一覧を参照）
  - ANTHROPIC_API_KEY, FITBIT_*, PGVECTOR_DSN, LANGFUSE_* を列挙
- [x] `.gitignore` に `.env` を追加
- [x] `.env` をコピーして実際の値を設定（gitignore 済み）

### Step 3: docker-compose.yml の作成
- [x] `docker-compose.yml` を workspace root に作成
- [x] pgvector サービス: `pgvector/pgvector:pg16`、ポート `5432`
- [x] LangFuse サービス: `langfuse/langfuse:2`、ポート `3000`
- [x] LangFuse 専用 DB: `postgres:16`、ポート `5433`
- [x] 各サービスの環境変数・ボリューム・depends_on を設定

### Step 4: ディレクトリ構造の作成
- [x] `agent/`, `tools/`, `fitbit/`, `memory/`, `tests/` ディレクトリを作成
- [x] 各ディレクトリに `__init__.py` を追加

---

## Phase 2: ドメインエンティティ（US-依存なし）

### Step 5: AgentState の実装
- [x] `agent/state.py` を作成
- [x] `AgentState(BaseModel)` を実装（`domain-entities.md` 参照）
  - `messages: Annotated[list[BaseMessage], add_messages]`
  - `session_id: str`
  - `model_config = {"arbitrary_types_allowed": True}`

### Step 6: その他エンティティの実装
- [x] `fitbit/models.py` を作成（FitbitData, TokenData）
- [x] `tools/models.py` を作成（WeightGoal, CalorieDeficitResult, WorkoutPlanInput, WorkoutPlan, WeeklyProgress, CalorieBalance）
- [x] `memory/models.py` を作成（MemoryEntry）
- [x] 全エンティティを Pydantic `BaseModel` で実装（`domain-entities.md` のコードを参照）
- [x] `WeightGoal` の `field_validator` を実装（pace 0.1〜1.0、target < current）
- [x] `CalorieDeficitResult` の `field_validator` を実装（deficit 200〜1000）

---

## Phase 3: インフラ層（メモリ・DB）

### Step 7: DB 初期化 SQL の作成
- [ ] `memory/init.sql` を作成
- [ ] pgvector extension 有効化: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] memories テーブル定義（`logical-components.md` LC-03 の DDL を参照）
  - `id UUID`, `session_id TEXT`, `content TEXT`, `embedding vector(1024)`, タイムスタンプ
- [ ] `session_id` インデックスを作成

### Step 8: EmbeddingModel Singleton の実装
- [ ] `memory/embedding.py` を作成
- [ ] `_model` モジュール変数（初期値 None）
- [ ] `get_embedding_model()` 関数: 初回のみ `SentenceTransformer("intfloat/multilingual-e5-large")` を初期化（PATTERN-01 参照）
- [ ] `embed(text: str) -> list[float]` 関数: `normalize_embeddings=True` でエンコード

### Step 9: ConnectionPool Singleton の実装
- [ ] `memory/connection_pool.py` を作成
- [ ] `_pool` モジュール変数（初期値 None）
- [ ] `get_pool()` 関数: `SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.getenv("PGVECTOR_DSN"))` を返す（PATTERN-02 参照）
- [ ] `get_connection()` / `release_connection(conn)` 関数

### Step 10: MemoryManager の実装
- [ ] `memory/manager.py` を作成
- [ ] `save_memory(session_id, content)` の実装
  - `embed(content)` でベクトル生成
  - pgvector に upsert（同一 session_id は上書き）
  - 接続は `get_connection()` / `finally: release_connection()` パターン（PATTERN-02）
  - エラー時は `logging.error` してサイレント失敗（PATTERN-03）
- [ ] `search_memories(session_id, query, limit=3)` の実装
  - `embed(query)` でクエリベクトル生成
  - `ORDER BY embedding <=> %s LIMIT %s` でコサイン類似度検索
  - エラー時は空リスト返却（PATTERN-03）

---

## Phase 4: Fitbit クライアント（US-02, US-04〜07）

### Step 11: FitbitClient の実装
- [ ] `fitbit/client.py` を作成
- [ ] `FitbitClient` クラスを実装
- [ ] `_get_valid_token()` の実装（US-02）
  - `.env` からトークンを読み込み
  - 有効期限 5 分前にリフレッシュ（BLM-06 参照）
  - リフレッシュ失敗時はエラー文字列を返す
- [ ] データ取得メソッドの共通パターン実装（BLM-07 参照）
  - `date: str = "today"`, `period: str | None = None` 引数
  - `period` 優先ルール（BR-02-2）
  - エラー時は `f"Error {status_code}: ..."` 文字列返却（BR-03, PATTERN-04）
- [ ] `get_activities(date, period)` → steps, calories_burned
- [ ] `get_body_data(date, period)` → weight_kg, bmi
- [ ] `get_heart_rate(date, period)` → heart_rate_avg
- [ ] `get_food_log(date)` → calories_in

---

## Phase 5: LangGraph ツール（US-04〜07, US-09〜13）

### Step 12: Fitbit ツールの実装
- [ ] `tools/fitbit_tools.py` を作成
- [ ] `FitbitClient` のインスタンスを取得する依存関係を定義
- [ ] `@tool` デコレータで以下を実装
  - `get_steps(date: str = "today", period: str | None = None) -> str`
  - `get_calories_burned(date: str = "today", period: str | None = None) -> str`
  - `get_weight(date: str = "today", period: str | None = None) -> str`
  - `get_heart_rate(date: str = "today", period: str | None = None) -> str`
  - `get_calories_in(date: str = "today") -> str`
- [ ] 各ツールは `FitbitClient` のメソッドを呼び出してレスポンスを文字列化して返す

### Step 13: プランニングツールの実装
- [ ] `tools/planning_tools.py` を作成
- [ ] `@tool` デコレータで以下を実装
  - `calculate_calorie_deficit(current_weight_kg: float, target_weight_kg: float, pace_kg_per_week: float = 0.5) -> str`
    - BLM-01 のアルゴリズムを実装
    - BR-01 の安全制約バリデーションを実装
    - `CalorieDeficitResult` で結果を構造化して返す
  - `generate_home_workout_plan(daily_deficit_kcal: int, fitness_level: str, available_days_per_week: int, duration_minutes: int) -> str`
    - BLM-02 の LLM 完全委任パターンで実装
    - ツール内で LLM を呼び出してプランを生成
  - `get_weekly_progress(current_weight_kg: float, start_weight_kg: float, target_pace_kg_per_week: float, weeks_elapsed: int) -> str`
    - BLM-04 のアルゴリズムを実装

---

## Phase 6: LangFuse セットアップ

### Step 14: LangFuse CallbackHandler の実装
- [ ] `agent/langfuse_setup.py` を作成
- [ ] `get_langfuse_handler()` 関数を実装（PATTERN-06 参照）
  - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` を `.env` から読み込む
  - `langfuse.callback.CallbackHandler` を返す

---

## Phase 7: LangGraph ノード・グラフ（US-09, US-14, US-15）

### Step 15: LangGraph ノードの実装
- [ ] `agent/nodes.py` を作成
- [ ] `memory_inject_node(state: AgentState) -> dict` の実装
  - `MemoryManager.search_memories()` で関連メモリを取得
  - メモリをシステムプロンプトの先頭に注入した messages を返す
- [ ] `agent_node(state: AgentState) -> dict` の実装
  - `langchain-anthropic` の `ChatAnthropic` でLLMを呼び出す
  - モデル: `claude-sonnet-4-6`
  - ツール一覧を bind_tools でバインド
  - メッセージ履歴を渡して応答を生成
- [ ] `tool_node(state: AgentState) -> dict` の実装
  - LangGraph 組み込みの `ToolNode` を使用、または手動実装
  - バインドされたツールを実行
- [ ] `memory_save_node(state: AgentState) -> dict` の実装
  - 会話全体を LLM で要約（BLM-05 参照）
  - `MemoryManager.save_memory()` で pgvector に保存
- [ ] `should_continue(state: AgentState) -> str` の実装
  - 最後のメッセージがツール呼び出しなら `"tool_node"` を返す
  - それ以外なら `"memory_save_node"` を返す

### Step 16: LangGraph グラフの実装
- [ ] `agent/graph.py` を作成
- [ ] `StateGraph(AgentState)` でグラフを定義
- [ ] ノードを追加: `memory_inject_node`, `agent_node`, `tool_node`, `memory_save_node`
- [ ] エッジを定義（BLM-08 のフロー図を参照）
  - `START → memory_inject_node → agent_node`
  - `agent_node` に条件分岐（`should_continue`）: `tool_node` or `memory_save_node`
  - `tool_node → agent_node`（ループ）
  - `memory_save_node → END`
- [ ] `InMemorySaver()` をチェックポインターとしてコンパイル
- [ ] `compile()` でグラフを確定、`agent` 変数に格納

---

## Phase 8: エントリポイント

### Step 17: main.py の実装
- [ ] `main.py` を作成
- [ ] 起動時に `get_embedding_model()` を呼び出してモデルをウォームアップ
- [ ] インタラクティブな REPL ループを実装
  - ユーザー入力を受け付ける
  - `session_id` を設定（例: UUID or 固定値）
  - `agent.stream()` でストリーミング実行（PATTERN-05 参照）
  - `config={"configurable": {"thread_id": session_id}, "callbacks": [get_langfuse_handler()]}` を渡す
  - `agent` チャンクの内容をターミナルにリアルタイム出力
- [ ] `docker-compose up -d` 後に `python main.py` で起動できることを確認

---

## Phase 9: テスト（PBT 含む）

### Step 18: ユニットテスト — ビジネスロジック（US-10, US-13）
- [ ] `tests/test_planning_tools.py` を作成
- [ ] `calculate_calorie_deficit` のユニットテスト
  - 正常系: 各パラメータの組み合わせで期待値を検証
  - 異常系: target >= current でエラー、pace > 1.0 でエラー
  - 境界値: pace = 0.1, 1.0
- [ ] `get_weekly_progress` のユニットテスト
  - 正常系: progress_ratio の計算値検証
  - 各 status（順調/やや遅れ/遅れ気味）のケース

### Step 19: PBT テスト（Hypothesis）— BR-09 プロパティ検証
- [ ] `tests/test_pbt_planning.py` を作成
- [ ] `PBT-09-1`: `calculate_calorie_deficit` の出力が常に安全範囲内（200〜1000kcal）
  ```python
  @given(
      current_weight=st.floats(50, 120),
      target_weight=st.floats(40, 119),
      pace=st.floats(0.1, 1.0)
  )
  def test_calorie_deficit_always_safe(current_weight, target_weight, pace):
      assume(target_weight < current_weight)
      result = calculate_calorie_deficit(current_weight, target_weight, pace)
      assert 200 <= result.daily_deficit_kcal <= 1000
  ```
- [ ] `PBT-09-2`: 体重減少に伴う `progress_ratio` の単調性
- [ ] `PBT-09-3`: `daily_deficit × 7 / 7200 ≈ pace` の逆算検証
- [ ] `PBT-09-4`: `period` 指定時は `date` が無視されることを検証

### Step 20: ユニットテスト — FitbitClient（US-02, US-04〜07）
- [ ] `tests/test_fitbit_client.py` を作成
- [ ] httpx の `respx` または `pytest-mock` でモック
- [ ] 正常系: 各メソッドのレスポンス解析を検証
- [ ] 異常系: 401, 429, 404, ネットワークエラーで正しいエラー文字列が返ることを確認
- [ ] トークンリフレッシュ: 期限切れトークンで `_get_valid_token()` がリフレッシュを呼ぶことを確認

### Step 21: ユニットテスト — MemoryManager（US-15）
- [ ] `tests/test_memory_manager.py` を作成
- [ ] psycopg2 をモックして pgvector クエリを検証
- [ ] `save_memory`: embedding が生成されて pgvector に渡されることを確認
- [ ] `search_memories`: コサイン類似度クエリが実行されることを確認
- [ ] Fallback: DB 接続エラー時に空リストが返ることを確認（PATTERN-03）

---

## Phase 10: 動作確認

### Step 22: Docker 起動 & DB 初期化
- [ ] `docker-compose up -d` で pgvector と LangFuse を起動
- [ ] `psql` で `memory/init.sql` を実行して memories テーブルを作成
- [ ] LangFuse ブラウザ (`http://localhost:3000`) でプロジェクトを作成し API キーを取得

### Step 23: エンドツーエンド動作確認
- [ ] `python main.py` を実行
- [ ] 以下のシナリオで動作確認
  1. 「今日の歩数を教えて」→ `get_steps` ツールが呼ばれる
  2. 「現在65kg、目標58kgにしたい」→ `calculate_calorie_deficit` が呼ばれる
  3. 「週3回30分で運動プランを作って」→ `generate_home_workout_plan` が呼ばれる
  4. 同一セッションで2回目の会話 → Short-term memory が機能していることを確認
  5. 再起動後に同一 session_id で会話 → Long-term memory が機能していることを確認
- [ ] LangFuse ダッシュボードでトレースを確認
- [ ] テストカバレッジ 80% 以上を確認: `pytest --cov=. --cov-report=term`

---

## 実装優先順位（依存関係順）

```
Step 1〜4 (セットアップ)
  ↓
Step 5〜6 (エンティティ)
  ↓
Step 7〜10 (インフラ: DB・Embedding・ConnectionPool・MemoryManager)
  ↓
Step 11 (FitbitClient)
  ↓
Step 12〜13 (ツール) ← FitbitClient に依存
  ↓
Step 14 (LangFuse)
  ↓
Step 15〜16 (ノード・グラフ) ← 全ツールに依存
  ↓
Step 17 (main.py)
  ↓
Step 18〜21 (テスト)
  ↓
Step 22〜23 (動作確認)
```
