# Logical Components — Unit 2: Backend API

## コンポーネント構成図

```
HTTP Client (curl / Frontend)
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│                     FastAPIApp (server.py)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CORSMiddleware                                        │  │
│  │  /chat   ──→  ChatController    (controllers/chat.py) │  │
│  │  /auth/* ──→  AuthController    (controllers/auth.py) │  │
│  │  /health ──→  HealthController  (controllers/health.py│  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐     ┌──────────────────────────┐
│  LangGraphAgent  │     │   FitbitService           │
│  (Unit 1 再利用) │     │  (services/fitbit_service)│
│  agent.astream() │     │  + state_store (dict)     │
└─────────────────┘     └──────────────┬───────────┘
                                        │
                                        ▼
                              ┌──────────────────────┐
                              │  UserRepository       │
                              │  (repositories/       │
                              │   user_repository.py) │
                              │  SELECT / INSERT /    │
                              │  UPDATE / DELETE      │
                              └──────────┬───────────┘
                                         │
                              ┌──────────┴───────────┐
                              │                       │
                              ▼                       ▼
                    ┌──────────────────┐  ┌──────────────────────┐
                    │  FitbitClient    │  │  PostgreSQL (pgvector)│
                    │  (fitbit/client) │  │  users テーブル        │
                    │  OAuth2 メソッド │  └──────────────────────┘
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────────┐
                    │  Fitbit OAuth2 API   │
                    │  (External)           │
                    └──────────────────────┘
```

---

## LC-01: FastAPIApp

**ファイル**: `server.py`

| 属性 | 内容 |
|---|---|
| 役割 | FastAPI アプリ初期化・ミドルウェア設定・ルーター登録 |
| 起動コマンド | `uv run uvicorn server:app --reload --port 8000` |

---

## LC-02: ChatController

**ファイル**: `app/controllers/chat.py`

| 属性 | 内容 |
|---|---|
| 役割 | POST /chat エンドポイント・Cookie 認証・SSE ジェネレータ |
| 依存 | `LangGraphAgent`（`agent/graph.py`）、`UserRepository`、`FitbitClient`、`AgentContext`、`ChatRequest` / `SSEChunk` |

**認証フロー**:
1. Cookie `fitbit_user_id` を取得（なければ 401）
2. `UserRepository.find_by_fitbit_user_id()` で DB 検索（なければ 401）
3. `User.is_token_expired()` でトークン有効期限確認（期限切れなら 401）
4. `FitbitClient` を生成し `set_fitbit_client()` で async コンテキストにセット
5. SSE ストリーミング開始

**インターフェース**:
```python
POST /chat  Cookie: fitbit_user_id=<id>  → StreamingResponse (text/event-stream)
            認証失敗時 → HTTPException (401)
async def _sse_generator(message: str, session_id: str) -> AsyncIterator[str]
```

---

## LC-03: AuthController

**ファイル**: `app/controllers/auth.py`

| 属性 | 内容 |
|---|---|
| 役割 | OAuth2 認可開始・コールバック処理・Cookie 発行 |
| 依存 | `FitbitService`（`app/services/fitbit_service.py`）、`AuthCallbackResponse`（`app/schemas/auth.py`） |

**インターフェース**:
```python
GET /auth/fitbit          → RedirectResponse (302)
GET /auth/fitbit/callback → AuthCallbackResponse (200)
                             + Set-Cookie: fitbit_user_id=<id>; HttpOnly; SameSite=Lax
                           | HTTPException (400)
```

**Cookie 仕様**:
- キー: `fitbit_user_id`
- HttpOnly: `True`（JavaScript からアクセス不可）
- SameSite: `lax`
- Secure: `False`（開発環境。本番は `True` + HTTPS 必須）

---

## LC-04: HealthController

**ファイル**: `app/controllers/health.py`

| 属性 | 内容 |
|---|---|
| 役割 | GET /health エンドポイント |
| 依存 | `HealthResponse`（`app/schemas/health.py`） |

**インターフェース**:
```python
GET /health → HealthResponse (200)
```

---

## LC-05: UserRepository

**ファイル**: `app/repositories/user_repository.py`

| 属性 | 内容 |
|---|---|
| 役割 | `users` テーブルの CRUD 操作を隠蔽する Repository レイヤ |
| 依存 | `psycopg2` 接続（`app/config/connection_pool.py` の `get_connection()` を使用） |

**インターフェース**:
```python
from datetime import datetime
from app.models.user import User

class UserRepository:
    def __init__(self, conn) -> None:
        self._conn = conn

    def find_by_fitbit_user_id(self, fitbit_user_id: str) -> User | None:
        """fitbit_user_id でユーザーを検索。存在しなければ None を返す。"""

    def upsert(self, user: User) -> None:
        """INSERT ... ON CONFLICT (fitbit_user_id) DO UPDATE でトークンを保存・更新する。"""

    def update_tokens(self, fitbit_user_id: str, access_token: str, refresh_token: str, token_expires_at: datetime) -> None:
        """トークンリフレッシュ時に access_token / refresh_token / token_expires_at を更新する。"""

    def delete(self, fitbit_user_id: str) -> None:
        """ユーザーレコードを削除する。"""
```

**upsert SQL**:
```sql
INSERT INTO users (fitbit_user_id, access_token, refresh_token, token_expires_at, scope, updated_at)
VALUES (%s, %s, %s, %s, %s, NOW())
ON CONFLICT (fitbit_user_id) DO UPDATE SET
    access_token     = EXCLUDED.access_token,
    refresh_token    = EXCLUDED.refresh_token,
    token_expires_at = EXCLUDED.token_expires_at,
    scope            = EXCLUDED.scope,
    updated_at       = NOW();
```

---

## LC-07: FitbitService

**ファイル**: `app/services/fitbit_service.py`

| 属性 | 内容 |
|---|---|
| 役割 | OAuth2 フロー全体の管理（state ストア・トークン交換・DB 保存） |
| 依存 | `FitbitClient`、`UserRepository`、`CsrfState` |

**インターフェース**:
```python
class FitbitService:
    def __init__(self, fitbit_client: FitbitClient, user_repository: UserRepository) -> None

    def get_authorization_url(self) -> tuple[str, str]:
        """(authorization_url, state_value) を返す。state_store に保存する。"""

    def exchange_code_for_token(self, code: str, state: str) -> TokenResponse:
        """state 検証 → トークン交換 → UserRepository.upsert() で DB 保存 → TokenResponse を返す。
        失敗時: InvalidStateError / StateExpiredError / TokenExchangeError を raise"""

    # 内部状態
    _state_store: dict[str, CsrfState]  # {state_value: CsrfState}
```

**カスタム例外**:
```python
class InvalidStateError(Exception): pass
class StateExpiredError(Exception): pass
class TokenExchangeError(Exception): pass
```

---

## LC-06: FitbitClient（OAuth2 メソッド追記）

**ファイル**: `fitbit/client.py`（Unit 1 の既存ファイルに追記）

Unit 1 で実装済みのデータ取得メソッドに、OAuth2 メソッドを追加する。

**追記するメソッド**:
```python
class FitbitClient:
    # --- Unit 1 の既存メソッド（変更なし） ---
    # get_activities(), get_body_data(), get_heart_rate(), get_food_log(), ...

    # --- Unit 2 で追記する OAuth2 メソッド ---

    def get_authorization_url(self, state: str) -> str:
        """OAuth2 認可 URL を生成して返す。"""
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "scope": "activity heartrate weight nutrition",
            "redirect_uri": self._redirect_uri,
            "state": state,
        }
        return f"https://www.fitbit.com/oauth2/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> TokenResponse:
        """認可コードをアクセストークンに交換する。
        失敗時は TokenExchangeError を raise。"""

    def refresh_access_token(self) -> TokenResponse:
        """リフレッシュトークンを使って新しいアクセストークンを取得する。
        失敗時は TokenRefreshError を raise。"""
```

**コンストラクタへの追加パラメータ**:
```python
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
```

---

## LC-08: DB 接続設定（ConnectionPool）

**ファイル**: `app/config/connection_pool.py`（`agent/memory/connection_pool.py` から移動）

| 属性 | 内容 |
|---|---|
| 役割 | psycopg2 コネクションプールの初期化・接続払い出し |
| 依存 | `psycopg2`、`PGVECTOR_DSN` 環境変数 |

**移動に伴う影響**:
- `agent/memory/manager.py` の import を `app.config.connection_pool` に更新する
- `app/repositories/user_repository.py` は `app.config.connection_pool` から `get_connection()` を使う

---

## LC-09: マイグレーション管理（Alembic）

**ディレクトリ**: `app/migrations/`

| 属性 | 内容 |
|---|---|
| 役割 | DB スキーマのバージョン管理 |
| ツール | Alembic |

**管理対象テーブル**:
- `memories`（Unit 1 既存 / pgvector 利用）
- `users`（Unit 2 新規追加）

**ディレクトリ構成**:
```
app/migrations/
├── env.py
├── script.py.mako
├── alembic.ini       ← プロジェクトルートに配置
└── versions/
    └── 0001_initial.py   ← memories + users テーブル
```

---

## LC-10: AgentContext（FitbitClient の per-request 受け渡し）

**ファイル**: `agent/context.py`

| 属性 | 内容 |
|---|---|
| 役割 | リクエストごとに独立した `FitbitClient` インスタンスを asyncio コンテキストで保持 |
| 実装 | Python 標準ライブラリ `contextvars.ContextVar` |
| 依存 | `agent.fitbit.client.FitbitClient` |

**背景**:
- `fitbit_tools.py` のツールはモジュールレベルで登録されており、リクエストごとに異なるトークンを渡す手段が必要
- `ContextVar` は asyncio タスクごとに独立した値を保持するため、並行リクエストでユーザーが混在しない
- sync 関数（`chat()`）から `set_fitbit_client()` を呼ぶと asyncio コンテキストに届かないため、async ジェネレーター（`_sse_generator`）の先頭で呼び出す

**インターフェース**:
```python
def set_fitbit_client(client: FitbitClient) -> None
def get_fitbit_client() -> FitbitClient  # 未設定時は RuntimeError
```

---

## 環境変数追加（.env）

Unit 1 の `.env` に以下を追記する:

```env
# FastAPI
API_HOST=0.0.0.0
API_PORT=8000

# Fitbit OAuth2 (Unit 2 で追加)
FITBIT_REDIRECT_URI=http://localhost:8000/auth/fitbit/callback
```

---

## ディレクトリ構成（Unit 2 追加分）

```
fitbit-agent/
├── server.py                          # FastAPI アプリ起動エントリポイント
├── alembic.ini                        # Alembic 設定
│
├── app/                               # バックエンド API（Unit 2）
│   ├── api/
│   │   └── router.py                  # ルーター集約
│   ├── controllers/                   # エンドポイント定義
│   │   ├── chat.py                    # POST /chat
│   │   ├── auth.py                    # GET /auth/fitbit*（新規）
│   │   └── health.py                  # GET /health
│   ├── services/
│   │   └── fitbit_service.py          # FitbitService（新規）
│   ├── repositories/
│   │   └── user_repository.py         # UserRepository（新規）
│   ├── models/                        # ドメインモデル（ロジックあり）
│   │   ├── auth.py                    # CsrfState
│   │   └── user.py                    # User
│   ├── schemas/                       # DTO（入出力の型定義）
│   │   ├── auth.py                    # TokenResponse, AuthCallbackResponse
│   │   ├── chat.py                    # ChatRequest, SSEChunk
│   │   └── health.py                  # HealthResponse
│   ├── config/
│   │   └── connection_pool.py         # psycopg2 接続プール
│   └── migrations/                    # Alembic マイグレーション
│       └── versions/
│           └── 1ca42141c7ae_initial.py
│
├── agent/                             # LangGraph エージェント（Unit 1）
│   ├── context.py                     # ContextVar: per-request FitbitClient 受け渡し（Unit 2 追加）
│   ├── fitbit/
│   │   └── client.py                  # Fitbit API クライアント
│   ├── memory/
│   │   ├── manager.py
│   │   └── embedding.py               # BedrockEmbeddings (Titan v2)
│   ├── tools/
│   │   ├── fitbit_tools.py            # get_fitbit_client() 経由でトークン取得
│   │   └── planning_tools.py
│   ├── graph.py
│   ├── nodes.py                       # ChatBedrockConverse (jp prefix, ap-northeast-1)
│   └── state.py
│
├── docker-compose.yml
├── pyproject.toml
└── .env
```
