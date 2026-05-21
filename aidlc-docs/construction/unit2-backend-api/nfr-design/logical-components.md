# Logical Components — Unit 2: Backend API

## コンポーネント構成図

```
HTTP Client (curl / Frontend)
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│                     FastAPIApp (main.py)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CORSMiddleware                                        │  │
│  │  /chat   ──→  ChatRouter (api/chat.py)               │  │
│  │  /auth/* ──→  AuthRouter (api/auth.py)               │  │
│  │  /health ──→  HealthRouter (api/health.py)           │  │
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
                              │  FitbitClient         │
                              │  (fitbit/client.py)   │
                              │  [Unit 1 既存メソッド] │
                              │  + OAuth2 メソッド追記 │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Fitbit OAuth2 API   │
                              │  (External)           │
                              └──────────────────────┘
```

---

## LC-01: FastAPIApp

**ファイル**: `main.py`

| 属性 | 内容 |
|---|---|
| 役割 | FastAPI アプリ初期化・ミドルウェア設定・ルーター登録 |
| 起動コマンド | `uv run uvicorn main:app --reload --port 8000` |

**実装**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.auth import router as auth_router
from api.health import router as health_router

app = FastAPI(title="Fitbit Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(health_router)
```

---

## LC-02: ChatRouter

**ファイル**: `api/chat.py`

| 属性 | 内容 |
|---|---|
| 役割 | POST /chat エンドポイント・SSE ジェネレータ |
| 依存 | `LangGraphAgent`（`agent/graph.py` からインポート） |

**インターフェース**:
```python
# エンドポイント
POST /chat → StreamingResponse (text/event-stream)

# SSE ジェネレータ（内部）
async def _sse_generator(message: str, session_id: str) -> AsyncIterator[str]
```

**LangGraphAgent の参照方法**:
```python
# api/chat.py
from agent.graph import get_agent  # Singleton パターンで取得

agent = get_agent()  # モジュールレベルで1回のみ初期化
```

---

## LC-03: AuthRouter

**ファイル**: `api/auth.py`

| 属性 | 内容 |
|---|---|
| 役割 | OAuth2 認可開始・コールバック処理エンドポイント |
| 依存 | `FitbitService`（`services/fitbit_service.py` からインポート） |

**インターフェース**:
```python
# エンドポイント
GET /auth/fitbit          → RedirectResponse (302)
GET /auth/fitbit/callback → AuthCallbackResponse (200) | HTTPException (400)
```

---

## LC-04: HealthRouter

**ファイル**: `api/health.py`

| 属性 | 内容 |
|---|---|
| 役割 | GET /health エンドポイント |
| 依存 | なし |

**インターフェース**:
```python
GET /health → HealthResponse (200)
```

---

## LC-05: FitbitService

**ファイル**: `services/fitbit_service.py`

| 属性 | 内容 |
|---|---|
| 役割 | OAuth2 フロー全体の管理（state ストア・トークン交換） |
| 依存 | `FitbitClient`、`OAuthState` |

**インターフェース**:
```python
class FitbitService:
    def __init__(self, fitbit_client: FitbitClient) -> None

    def get_authorization_url(self) -> tuple[str, str]:
        """(authorization_url, state_value) を返す。state_store に保存する。"""

    def exchange_code_for_token(self, code: str, state: str) -> TokenResponse:
        """state 検証 → トークン交換 → TokenResponse を返す。
        失敗時: InvalidStateError / StateExpiredError / TokenExchangeError を raise"""

    # 内部状態
    _state_store: dict[str, OAuthState]  # {state_value: OAuthState}
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
├── main.py                        # FastAPI アプリ初期化（新規）
├── api/
│   ├── __init__.py
│   ├── chat.py                    # POST /chat（新規）
│   ├── auth.py                    # GET /auth/fitbit*（新規）
│   └── health.py                  # GET /health（新規）
├── services/
│   ├── __init__.py
│   └── fitbit_service.py          # FitbitService（新規）
├── models/
│   ├── __init__.py
│   └── api_models.py              # ChatRequest, SSEChunk, AuthCallbackResponse 等（新規）
├── fitbit/
│   └── client.py                  # OAuth2 メソッドを追記（既存ファイル更新）
│
│ --- Unit 1 の既存ファイル（変更なし）---
├── agent/
│   ├── graph.py
│   ├── nodes.py
│   └── state.py
├── tools/
│   ├── fitbit_tools.py
│   └── planning_tools.py
├── memory/
│   ├── manager.py
│   ├── embedding.py
│   └── connection_pool.py
├── docker-compose.yml
├── pyproject.toml
└── .env
```
