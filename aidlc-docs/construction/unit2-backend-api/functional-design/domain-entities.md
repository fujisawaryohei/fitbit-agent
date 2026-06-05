# Domain Entities — Unit 2: Backend API

## エンティティ一覧

| エンティティ　　　　 | 説明　　　　　　　　　　　　　　　　　　　　　| 関連ストーリー |
| ----------------------| -----------------------------------------------| ----------------|
| ChatRequest　　　　　| POST /chat のリクエストボディ　　　　　　　　 | US-09〜15　　　|
| ChatResponse　　　　 | POST /chat の非SSE時レスポンス（エラー用）　　| US-09〜15　　　|
| SSEChunk　　　　　　 | SSEストリーミングのチャンク単位　　　　　　　 | US-09〜15　　　|
| OAuthState　　　　　 | OAuth2 CSRF防止用 state トークン　　　　　　　| US-01〜03　　　|
| TokenResponse　　　　| Fitbit API から受け取るトークンレスポンス　　 | US-01〜03　　　|
| AuthCallbackResponse | /auth/fitbit/callback の成功レスポンス　　　　| US-01〜03　　　|
| User　　　　　　　　 | Fitbit ユーザーとそのトークン情報（DB永続化） | US-01〜03　　　|
| HealthResponse　　　 | GET /health のレスポンス　　　　　　　　　　　| —　　　　　　　|

---

## ChatRequest

POST /chat のリクエストボディ。

```python
class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("messageを空文字列にすることはできません")
        if len(v) > 2000:
            raise ValueError("messageは2000文字以内で入力してください")
        return v
```

> ※ `session_id` は設計当初含まれていたが実装では削除。session_id は `user.id` をサーバー側で管理する。

---

## SSEChunk

SSEストリーミングの1チャンク単位。`data: {json}\n\n` 形式で送信する。

```python
class SSEChunk(BaseModel):
    type: Literal["chunk", "done", "error"]
    content: str = ""
    session_id: str = ""
    chat_id: int | None = None    # type="done" 時にフロントへ chat_id を通知
```

**送信フォーマット**:
```
data: {"type": "chunk", "content": "こんにちは", "session_id": "1"}\n\n
data: {"type": "done", "content": "", "session_id": "1", "chat_id": 42}\n\n
data: {"type": "error", "content": "...", "session_id": "1"}\n\n
```

---

## ChatSummaryResponse / ChatMessageResponse

会話履歴 API のレスポンス。

```python
class ChatSummaryResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

class ChatMessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime
```

---

## OAuthState

OAuth2 CSRF防止用の state パラメータ。認可リクエスト時に生成し、callback 時に検証する。

```python
from pydantic import BaseModel
from datetime import datetime
import secrets

class OAuthState(BaseModel):
    value: str
    created_at: datetime

    @classmethod
    def generate(cls) -> "OAuthState":
        return cls(
            value=secrets.token_urlsafe(32),
            created_at=datetime.utcnow()
        )

    def is_expired(self, ttl_seconds: int = 600) -> bool:
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > ttl_seconds
```

**設計方針**: PoC スコープでは state をプロセスメモリ（dict）に保存する。複数ユーザー・複数プロセスへの拡張時は Redis 等のセッションストアへ移行する。

---

## TokenResponse

Fitbit OAuth2 API から受け取るトークンレスポンスの型定義。

```python
from pydantic import BaseModel
from datetime import datetime, timedelta

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int           # 秒数（通常 28800 = 8時間）
    token_type: str           # "Bearer"
    scope: str                # 付与されたスコープのスペース区切り文字列
    user_id: str              # Fitbit ユーザーID

    def expires_at(self) -> datetime:
        return datetime.utcnow() + timedelta(seconds=self.expires_in)
```

---

## AuthCallbackResponse

GET /auth/fitbit/callback の成功レスポンス。

```python
from pydantic import BaseModel

class AuthCallbackResponse(BaseModel):
    message: str = "Fitbit認証が完了しました"
    fitbit_user_id: str
    scope: str
```

---

## User

Fitbit ユーザーの認証情報を保持するドメインエンティティ。PostgreSQL の `users` テーブルに永続化する。

```python
class User:
    def __init__(
        self,
        fitbit_user_id: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        scope: str,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None: ...

    def is_token_expired(self, buffer_minutes: int = 5) -> bool:
        """バッファ付きでトークン有効期限を確認する。"""
```

> ※ dataclass ではなく通常クラスで実装。`id` は DB 挿入前は `None`、挿入後は `int`。

---

## Chat / Message

会話履歴を保持するドメインエンティティ。

```python
class Chat:
    def __init__(
        self,
        user_id: int,
        title: str,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None: ...

class Message:
    def __init__(
        self,
        chat_id: int,
        role: MessageRole,
        content: str,
        id: int | None = None,
        created_at: datetime | None = None,
    ) -> None: ...
```

**DB スキーマ**:
```sql
CREATE TABLE chats (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    title      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE messages (
    id         SERIAL PRIMARY KEY,
    chat_id    INTEGER NOT NULL REFERENCES chats(id),
    role       VARCHAR(20) NOT NULL,  -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**DB スキーマ**:
```sql
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    fitbit_user_id   VARCHAR(255) UNIQUE NOT NULL,
    access_token     TEXT NOT NULL,
    refresh_token    TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scope            TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**設計方針**:
- `fitbit_user_id` で一意に識別する（Fitbit API が返す `user_id`）
- トークンは `UserRepository.upsert()` で INSERT / UPDATE を一本化する
- 複数ユーザー対応: `fitbit_user_id` を毎回 `FitbitClient` に渡してトークンを引く

---

## HealthResponse

GET /health のレスポンス。

```python
from pydantic import BaseModel
from typing import Literal

class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str = "1.0.0"
```

---

## エンティティ関係図

```
HTTP Request
    │
    ▼
ChatRequest ─────────────────────────────────────→ LangGraphAgent.stream()
  (message, session_id)                                    │
                                                           ▼
                                                      SSEChunk (type=chunk)
                                                      SSEChunk (type=done)
                                                      SSEChunk (type=error)

GET /auth/fitbit ──→ OAuthState.generate() ──→ redirect → Fitbit OAuth2
                          │
                          └──→ state_store[state.value] = state

GET /auth/fitbit/callback (code, state)
    ├─ OAuthState.is_expired() 検証
    ├─ FitbitClient.exchange_code_for_token(code) ──→ TokenResponse
    └─ AuthCallbackResponse ──→ HTTP 200

GET /health ──→ HealthResponse
```

---

## Unit 1 エンティティとの関係

| Unit 1 エンティティ | Unit 2 での利用 |
|---|---|
| `TokenData` | `FitbitClient` が `.env` から読み込む（Unit 1）→ Unit 2 では `TokenResponse` から更新 |
| `AgentState` | `LangGraphAgent.stream()` 内部で使用（Unit 2 から直接参照しない） |
