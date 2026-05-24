# Code Generation Plan — Unit 2: Backend API

> **ペアプロ方針**: ナビゲーター(Claude) / ドライバー(ユーザー)形式で進める。
> 機能が必要になったタイミングでコンポーネントを追加する。1ステップのスコープは最小限。

## 設計アーティファクト参照先

| 種別 | ファイル |
|---|---|
| ビジネスロジック | `aidlc-docs/construction/unit2-backend-api/functional-design/business-logic-model.md` |
| ドメインエンティティ | `aidlc-docs/construction/unit2-backend-api/functional-design/domain-entities.md` |
| ビジネスルール | `aidlc-docs/construction/unit2-backend-api/functional-design/business-rules.md` |
| NFRパターン | `aidlc-docs/construction/unit2-backend-api/nfr-design/nfr-design-patterns.md` |
| 論理コンポーネント | `aidlc-docs/construction/unit2-backend-api/nfr-design/logical-components.md` |

---

## Milestone 1: GET /health が動く

**追加するもの**: FastAPI の最小構成のみ

### Step 1: 依存ライブラリの追加

- [x] `pyproject.toml` に `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0` を追加
- [x] `uv sync` を実行

### Step 2: ディレクトリ作成

- [x] `api/` ディレクトリ + `__init__.py`
- [x] `models/` ディレクトリ + `__init__.py`

### Step 3: HealthResponse モデルの追加

- [x] `models/health.py` を新規作成
- [x] `HealthResponse` のみ追加（`status: Literal["ok"]`, `version: str = "1.0.0"`）

### Step 4: health エンドポイントの実装

- [x] `api/health.py` を作成
- [x] `GET /health → HealthResponse(status="ok")` を実装

### Step 5: FastAPI アプリの起動設定

- [x] `api/router.py` を作成（全ルーターの集約ポイント）
- [x] `app.py` を作成（`main.py` は Unit 1 の REPL と干渉しないよう別ファイルにする）
  - `FastAPI` インスタンス生成 + `CORSMiddleware`（`localhost:3000` のみ）
  - `api/router.py` 経由で `health_router` を登録

### Milestone 1 動作確認

- [x] `uv run uvicorn app:app --reload --port 8000` でサーバー起動
- [x] `curl http://localhost:8000/health` → `{"status":"ok","version":"1.0.0"}` を確認
- [x] `http://localhost:8000/docs` で Swagger UI が開くことを確認

---

## Milestone 2: POST /chat SSE が動く

**追加するもの**: チャット機能に必要なモデルとルーターのみ

### Step 6: ChatRequest / SSEChunk モデルの追加

- [x] `models/chat.py` を新規作成
- [x] `ChatRequest` を追加（`message`（空禁止・2000文字以内）、`session_id`（空禁止）の `field_validator`）
- [x] `SSEChunk` を追加（`type: Literal["chunk", "done", "error"]`, `content: str = ""`, `session_id: str = ""`）

### Step 7: agent に astream 対応の取得口を追加

- [x] `agent/graph.py` の末尾に `get_agent()` 関数を1行追記
  ```python
  def get_agent():
      return agent
  ```

### Step 8: chat エンドポイントの実装

- [x] `api/chat.py` を作成
  - モジュールレベルで `_agent = get_agent()`
  - `POST /chat → StreamingResponse(media_type="text/event-stream")`
    - ヘッダー: `Cache-Control: no-cache`, `X-Accel-Buffering: no`
  - `async def _sse_generator(message, session_id)` を実装
    - `_agent.astream()` を `async for` でイテレート
    - `"agent"` キーのチャンクから `content` を抽出 → `SSEChunk(type="chunk")` を yield
    - 完了時 → `SSEChunk(type="done")` を yield
    - 例外時 → `SSEChunk(type="error", content=str(e))` を yield

### Step 9: app.py に chat_router を追加

- [x] `api/router.py` に `chat_router` を追加

### Milestone 2 動作確認

- [x] SSE ストリーミングを確認:
  ```bash
  curl -N -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "こんにちは", "session_id": "test-001"}'
  ```
  → `data: {"type":"chunk",...}` が順次届き、最後に `type:"done"` が届くことを確認
- [ ] ツール呼び出しを確認:
  ```bash
  curl -N -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "今日の歩数を教えて", "session_id": "test-001"}'
  ```
  → LangSmith で `get_steps` ツールのトレースが記録されていることを確認

---

## Milestone 3: OAuth2 フローが動く

**追加するもの**: OAuth2 に必要なモデル・サービス・ルーターのみ

### Step 9b: connection_pool の移動と Alembic セットアップ

- [ ] `app/config/` ディレクトリ + `__init__.py` を作成
- [ ] `agent/memory/connection_pool.py` を `app/config/connection_pool.py` にコピー
- [ ] `agent/memory/connection_pool.py` の内容を `app.config.connection_pool` への re-export に差し替え（後方互換）
- [ ] `agent/memory/manager.py` の import を `app.config.connection_pool` に更新
- [ ] `pyproject.toml` の依存に `alembic>=1.14.0` を追加し `uv sync`
- [ ] `uv run alembic init app/migrations` を実行
- [ ] `alembic.ini` の `script_location` を `app/migrations` に設定
- [ ] `app/migrations/env.py` の `sqlalchemy.url` を `PGVECTOR_DSN` 環境変数から取得するよう設定
- [ ] 初回マイグレーションファイル `versions/0001_initial.py` を作成
  - `memories` テーブル（`id`, `session_id`, `content`, `embedding vector(1536)`, `created_at`）
  - `users` テーブル（domain-entities.md の DDL 参照）
- [ ] `uv run alembic upgrade head` でマイグレーション適用・確認

### Step 10: OAuth2 モデルの追加

- [ ] `models/auth.py` を新規作成
- [ ] `OAuthState` を追加
  - `value: str`, `created_at: datetime`
  - `generate()` クラスメソッド（`secrets.token_urlsafe(32)` で生成）
  - `is_expired(ttl_seconds=600) -> bool` メソッド
- [ ] `TokenResponse` を追加
  - `access_token`, `refresh_token`, `expires_in`, `token_type`, `scope`, `user_id`
  - `expires_at() -> datetime` メソッド
- [ ] `AuthCallbackResponse` を追加
  - `message: str = "Fitbit認証が完了しました"`, `fitbit_user_id: str`, `scope: str`

### Step 11: FitbitClient に OAuth2 メソッドを追記

- [ ] `fitbit/client.py` の `FitbitClient.__init__` に `redirect_uri` パラメータを追加
  - `redirect_uri: str = os.getenv("FITBIT_REDIRECT_URI", "http://localhost:8000/auth/fitbit/callback")`
- [ ] `get_authorization_url(state: str) -> str` を追記
  - スコープ: `activity heartrate weight nutrition`
  - `https://www.fitbit.com/oauth2/authorize?...` の URL を組み立てて返す
- [ ] `exchange_code_for_token(code: str) -> TokenResponse` を追記
  - `POST https://api.fitbit.com/oauth2/token`
  - Basic 認証（`client_id:client_secret` を Base64 エンコード）
  - 失敗時は `TokenExchangeError` を raise
- [ ] `refresh_access_token() -> TokenResponse` を追記
  - `POST https://api.fitbit.com/oauth2/token`（`grant_type=refresh_token`）
  - 失敗時は `TokenRefreshError` を raise

### Step 12: User モデルの追加

- [ ] `app/models/user.py` を新規作成
  - `User` dataclass（`fitbit_user_id`, `access_token`, `refresh_token`, `token_expires_at`, `scope`, `id`, `created_at`, `updated_at`）

### Step 12b: UserRepository の実装

- [ ] `app/repositories/` ディレクトリ + `__init__.py`
- [ ] `app/repositories/user_repository.py` を作成
  - `UserRepository.__init__(conn)`: psycopg2 接続を受け取る
  - `find_by_fitbit_user_id(fitbit_user_id: str) -> User | None`
  - `upsert(user: User) -> None`（INSERT ... ON CONFLICT DO UPDATE）
  - `update_tokens(fitbit_user_id, access_token, refresh_token, token_expires_at) -> None`
  - `delete(fitbit_user_id: str) -> None`
  - `get_user_repository()` ファクトリ関数（`get_connection()` を使用）

### Step 12c: FitbitService の実装

- [ ] `app/services/` ディレクトリ + `__init__.py`
- [ ] `app/services/fitbit_service.py` を作成
  - カスタム例外: `InvalidStateError`, `StateExpiredError`, `TokenExchangeError`
  - `FitbitService.__init__(fitbit_client, user_repository)`: `_state_store: dict[str, CsrfState] = {}` を保持
  - `get_authorization_url() -> tuple[str, str]`（URL と state 値を返す）
  - `exchange_code_for_token(code, state) -> TokenResponse`（state 検証 → トークン交換 → `user_repository.upsert()` で DB 保存）
  - `get_fitbit_service()` Singleton ファクトリ関数

### Step 13: auth エンドポイントの実装

- [ ] `api/auth.py` を作成
  - モジュールレベルで `_service = get_fitbit_service()`
  - `GET /fitbit → RedirectResponse(url, status_code=302)`
  - `GET /fitbit/callback?code&state → AuthCallbackResponse`
    - カスタム例外を `HTTPException(400)` に変換

### Step 14: app.py に auth_router を追加

- [ ] `app.py` に `app.include_router(auth_router, prefix="/auth")` を1行追記

### Milestone 3 動作確認

- [ ] ブラウザで `http://localhost:8000/auth/fitbit` にアクセス
  → Fitbit 認可ページ（`www.fitbit.com/oauth2/authorize`）にリダイレクトされることを確認
- [ ] Fitbit で認可後、callback が受信されることを確認
  → `{"message": "Fitbit認証が完了しました", "fitbit_user_id": "...", "scope": "..."}` が返ることを確認

---

## Milestone 4: テスト

**追加するもの**: 各エンドポイント・サービスのテストを機能単位で追加

### Step 15: テスト用依存ライブラリの追加

- [ ] `pyproject.toml` dev 依存に `pytest-asyncio>=0.24.0` を追加
- [ ] `pyproject.toml` dev 依存に `respx>=0.21.0` を追加
- [ ] `pyproject.toml` に `[tool.pytest.ini_options]` を追加
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  ```
- [ ] `uv sync` を実行

### Step 16: /health のテスト

- [ ] `tests/test_api_health.py` を作成
  - `GET /health` → 200, `{"status": "ok", "version": "1.0.0"}`

### Step 17: /chat のテスト

- [ ] `tests/test_api_chat.py` を作成
  - 正常系: `astream()` をモックして `type:"chunk"` → `type:"done"` の順を確認
  - エラー系: `astream()` が例外を投げたとき `type:"error"` チャンクを確認
  - バリデーション: `message=""` → 422, `message` 2001文字 → 422, `session_id=""` → 422

### Step 18: FitbitService のテスト

- [ ] `tests/test_fitbit_service.py` を作成
  - `get_authorization_url()`: URL に `client_id`, `scope`, `redirect_uri`, `state` が含まれることを確認
  - `exchange_code_for_token()` 正常系: `TokenResponse` が返ることを確認
  - `exchange_code_for_token()` エラー: state 不一致 → `InvalidStateError`
  - `exchange_code_for_token()` エラー: 期限切れ → `StateExpiredError`
  - リプレイ防止: 同じ state で2回呼ぶ → 2回目は `InvalidStateError`

### Step 19: FitbitClient OAuth2 メソッドのテスト

- [ ] `tests/test_fitbit_client.py` に OAuth2 メソッドのテストを追記（`respx` でモック）
  - `get_authorization_url()`: クエリパラメータの検証
  - `exchange_code_for_token()` 正常系: `TokenResponse` への変換を確認
  - `exchange_code_for_token()` エラー系: Fitbit API 400 → `TokenExchangeError`

### Step 20: カバレッジ確認

- [ ] `uv run pytest --cov=. --cov-report=term --ignore=tests/test_planning_tools_llm.py` でカバレッジ 80% 以上を確認
