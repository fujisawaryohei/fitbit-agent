# Logical Components — Unit 2: Backend API

## コンポーネント構成図

```
HTTP Client (Browser / Frontend)
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│                     FastAPIApp (server.py)                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  CORSMiddleware                                          │    │
│  │  POST /chat              ──→  ChatController            │    │
│  │  GET  /chats             ──→  ChatController            │    │
│  │  GET  /chats/{id}/messages──→ ChatController            │    │
│  │  GET  /auth/fitbit       ──→  AuthController            │    │
│  │  GET  /auth/fitbit/callback──→AuthController            │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  DIContainer (containers.py)  ← dependency-injector             │
│    conn        → psycopg2 コネクション                           │
│    user_repo   → UserRepository(conn)                           │
│    chat_repo   → ChatRepository(conn)                           │
│    message_repo→ MessageRepository(conn)                        │
│    fitbit_client → FitbitClient                                  │
│    fitbit_service→ FitbitService (Singleton)                    │
└────────────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐     ┌──────────────────────────┐
│  LangGraphAgent  │     │   FitbitService           │
│  (Unit 1 再利用) │     │  (services/fitbit_service)│
│  agent.astream() │     │  + state_store (dict)     │
└─────────────────┘     └──────────────┬───────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────┐
                    │  Repositories                      │
                    │  UserRepository    (users)         │
                    │  ChatRepository    (chats)         │
                    │  MessageRepository (messages)      │
                    └───────────────┬───────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  PostgreSQL (pgvector)│
                         │  users / chats /      │
                         │  messages テーブル     │
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

**ファイル**: `backend/controllers/chat.py`

| 属性 | 内容 |
|---|---|
| 役割 | チャット送信・会話履歴取得エンドポイント・Cookie 認証・SSE ジェネレータ |
| 依存 | `LangGraphAgent`、`UserRepository`、`ChatRepository`、`MessageRepository`、`FitbitClient`、`AgentContext` |

**エンドポイント**:
```python
POST /chat                        → StreamingResponse (text/event-stream)
GET  /chats                       → list[ChatSummaryResponse]
GET  /chats/{chat_id}/messages    → list[ChatMessageResponse]
```

**認証フロー（共通）**:
1. Cookie `fitbit_user_id` を取得（なければ 401）
2. `UserRepository.find_by_fitbit_user_id()` で DB 検索（なければ 401）
3. `assert user.id is not None`（DB から取得したユーザーは必ず id を持つ）

**SSE生成の注意点**:
- `_sse_generator` の conn は DI に委ねず手動取得・手動解放する
- `StreamingResponse` 返却後もストリーミングが続くため、DI の yield クリーンアップが早期実行されるのを防ぐため

---

## LC-03: AuthController

**ファイル**: `backend/controllers/auth.py`

| 属性 | 内容 |
|---|---|
| 役割 | OAuth2 認可開始・コールバック処理・Cookie 発行 |
| 依存 | `FitbitService`、`masked_credentials` デコレーター |

**インターフェース**:
```python
GET /auth/fitbit          → RedirectResponse (302) → Fitbit 認可画面
GET /auth/fitbit/callback → RedirectResponse (302) → FRONTEND_URL
                             + Set-Cookie: fitbit_user_id=<id>; HttpOnly; SameSite=Lax
                             + Set-Cookie: fitbit_connected=true; SameSite=Lax
                           | HTTPException (400) → 不正 state / 期限切れ
```

**Cookie 仕様**:
- `fitbit_user_id`: HttpOnly=True（JavaScript からアクセス不可）
- `fitbit_connected`: HttpOnly=False（フロントの接続状態表示に使用）
- SameSite: `lax`
- Secure: `False`（開発環境。本番は `True` + HTTPS 必須）

**ログマスク**:
- `@masked_credentials("code", "state")` を適用
- アクセスログに認可コード・state が平文出力されるのを防ぐ

---

## LC-04: HealthController

**ファイル**: `backend/controllers/health.py`

| 属性 | 内容 |
|---|---|
| 役割 | GET /health エンドポイント |
| 依存 | `HealthResponse`（`backend/schemas/health.py`） |

**インターフェース**:
```python
GET /health → HealthResponse (200)
```

---

## LC-05: UserRepository

**ファイル**: `backend/repositories/user_repository.py`

| 属性 | 内容 |
|---|---|
| 役割 | `users` テーブルの CRUD 操作を隠蔽する Repository レイヤ |
| 依存 | `psycopg2.extensions.connection` |

**インターフェース**:
```python
class UserRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None: ...
    def find_by_fitbit_user_id(self, fitbit_user_id: str) -> User | None: ...
    def upsert(self, user: User) -> None: ...
    def update_tokens(self, fitbit_user_id: str, access_token: str,
                      refresh_token: str, token_expires_at: datetime) -> None: ...
```

---

## LC-05b: ChatRepository

**ファイル**: `backend/repositories/chat_repository.py`

| 属性 | 内容 |
|---|---|
| 役割 | `chats` テーブルの CRUD 操作 |
| 依存 | `psycopg2.extensions.connection` |

**インターフェース**:
```python
class ChatRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None: ...
    def get_all(self, user_id: int) -> list[Chat]: ...
    def find_by_id(self, id: int) -> Chat | None: ...
    def insert(self, chat: Chat) -> int: ...       # RETURNING id
    def delete_by_id(self, id: int) -> None: ...
```

---

## LC-05c: MessageRepository

**ファイル**: `backend/repositories/message_repository.py`

| 属性 | 内容 |
|---|---|
| 役割 | `messages` テーブルの CRUD 操作 |
| 依存 | `psycopg2.extensions.connection` |

**インターフェース**:
```python
class MessageRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None: ...
    def get_all(self, chat_id: int) -> list[Message]: ...
    def insert(self, message: Message) -> None: ...
```

---

## LC-05d: DIContainer

**ファイル**: `backend/containers.py`

| 属性 | 内容 |
|---|---|
| 役割 | dependency-injector によるDI管理。各リポジトリ・サービスのライフサイクルを一元管理 |

**プロバイダ定義**:
```python
conn          = providers.Resource(_create_conn)       # yield コネクション
user_repo     = providers.Factory(UserRepository, conn=conn)
chat_repo     = providers.Factory(ChatRepository, conn=conn)
message_repo  = providers.Factory(MessageRepository, conn=conn)
fitbit_client = providers.Singleton(_create_fitbit_client)
fitbit_service= providers.Singleton(FitbitService, ...)
```

`FitbitService` を `Singleton` にする理由: 内部の `state_store`（CSRF トークン）をリクエスト間で共有する必要があるため。

---

## LC-07: FitbitService

**ファイル**: `backend/services/fitbit_service.py`

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

    def exchange_code_for_token(self, code: str | None, state: str | None) -> User:
        """state 検証 → code None チェック → トークン交換 → UserRepository.upsert() で DB 保存。
        失敗時: InvalidStateError / StateExpiredError を raise"""

    _state_store: dict[str, CsrfState]
```

**カスタム例外**:
```python
class InvalidStateError(Exception): pass   # state 不正 / code=None
class StateExpiredError(Exception): pass   # state 期限切れ
```

---

## LC-11: MaskedCredentials（デコレーター）

**ファイル**: `backend/decorators/masked_credentials.py`

| 属性 | 内容 |
|---|---|
| 役割 | uvicorn アクセスログの指定クエリパラメータ値を `***` に置換する |

**使い方**:
```python
@router.get("/auth/fitbit/callback")
@masked_credentials("code", "state")
def callback(...): ...
```

**仕組み**:
1. `@masked_credentials("code", "state")` でマスク対象パラメータを登録
2. `setup_access_log_masking()` を `server.py` 起動時に呼び出し `uvicorn.access` ロガーにフィルターを追加
3. ログ出力時に `?code=abc123&state=xyz` → `?code=***&state=***` に置換

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

**ファイル**: `backend/config/connection_pool.py`（`agent/memory/connection_pool.py` から移動）

| 属性 | 内容 |
|---|---|
| 役割 | psycopg2 コネクションプールの初期化・接続払い出し |
| 依存 | `psycopg2`、`PGVECTOR_DSN` 環境変数 |

**移動に伴う影響**:
- `agent/memory/manager.py` の import を `backend.config.connection_pool` に更新する
- `backend/repositories/user_repository.py` は `backend.config.connection_pool` から `get_connection()` を使う

---

## LC-09: マイグレーション管理（Alembic）

**ディレクトリ**: `backend/migrations/`

| 属性 | 内容 |
|---|---|
| 役割 | DB スキーマのバージョン管理 |
| ツール | Alembic |

**管理対象テーブル**:
- `memories`（Unit 1 既存 / pgvector 利用）
- `users`（Unit 2 新規追加）

**ディレクトリ構成**:
```
backend/migrations/
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
├── backend/                            # バックエンド API（Unit 2）
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
