# NFR Design Patterns — Unit 2: Backend API

## 適用パターン一覧

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Async SSE Generator | ChatRouter | LangGraph astream() をSSEチャンクに変換してリアルタイム送信 |
| State Store（In-memory dict） | FitbitService | OAuth2 CSRF防止 state の一時保存 |
| Router 分離 | FastAPIApp | エンドポイント群をドメインごとにファイル分割 |
| Dependency Injection（モジュールレベル Singleton） | ChatRouter | LangGraphAgent インスタンスをルーター間で共有 |
| カスタム例外 → HTTP エラー変換 | AuthRouter | サービス層の例外を FastAPI HTTPException に変換 |

---

## PATTERN-01: Async SSE Generator

### 問題
LangGraph の `agent.astream()` は非同期ジェネレータを返すが、FastAPI の `StreamingResponse` に渡すには `async def` ジェネレータ関数が必要。
また、SSE のフォーマット（`data: {json}\n\n`）への変換と、エラー時の正常終了処理が必要。

### 解決策
内部の `async def _sse_generator()` 関数で変換・エラーハンドリングを行い、`StreamingResponse` に渡す。

```python
# api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from agent.graph import get_agent
from models.api_models import ChatRequest, SSEChunk

router = APIRouter()
_agent = get_agent()  # モジュールレベルで1回初期化

@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_generator(request.message, request.session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

async def _sse_generator(message: str, session_id: str):
    try:
        async for chunk in _agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": session_id}},
        ):
            if "agent" in chunk:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        data = SSEChunk(
                            type="chunk",
                            content=msg.content,
                            session_id=session_id,
                        )
                        yield f"data: {data.model_dump_json()}\n\n"
        yield f"data: {SSEChunk(type='done', session_id=session_id).model_dump_json()}\n\n"
    except Exception as e:
        yield f"data: {SSEChunk(type='error', content=str(e), session_id=session_id).model_dump_json()}\n\n"
```

### トレードオフ
- **メリット**: ビジネスロジック（エラー処理・フォーマット変換）がエンドポイント関数から分離される
- **デメリット**: クライアント切断時の `CancelledError` は FastAPI が自動処理するが、後処理が必要な場合は `try/finally` を追加する必要がある

---

## PATTERN-02: State Store（In-memory dict）

### 問題
OAuth2 認可フローでは、認可リクエスト時に生成した `state` を callback で検証する必要がある。セッション間でデータを保持できる保管場所が必要。

### 解決策
`FitbitService` 内にプロセスメモリの dict を保持する。PoC スコープのため外部ストア（Redis 等）は不要。

```python
# services/fitbit_service.py
from models.api_models import OAuthState

class FitbitService:
    def __init__(self, fitbit_client: FitbitClient) -> None:
        self._client = fitbit_client
        self._state_store: dict[str, OAuthState] = {}

    def get_authorization_url(self) -> tuple[str, str]:
        state = OAuthState.generate()
        self._state_store[state.value] = state
        url = self._client.get_authorization_url(state.value)
        return url, state.value

    def exchange_code_for_token(self, code: str, state: str) -> TokenResponse:
        stored = self._state_store.get(state)
        if stored is None:
            raise InvalidStateError("state が見つかりません")
        if stored.is_expired():
            del self._state_store[state]
            raise StateExpiredError("state の有効期限が切れています")
        del self._state_store[state]  # リプレイ攻撃防止
        return self._client.exchange_code_for_token(code)
```

### トレードオフ
- **メリット**: シンプル、外部依存なし、PoC に適している
- **デメリット**: プロセス再起動で state が失われる（PoC では許容）、複数プロセス不可

---

## PATTERN-03: Router 分離

### 問題
すべてのエンドポイントを `main.py` に記述すると、コードが肥大化して保守性が低下する。

### 解決策
ドメイン（chat・auth・health）ごとに `APIRouter` を別ファイルに定義し、`main.py` で `include_router()` する。

```python
# main.py
from api.chat import router as chat_router
from api.auth import router as auth_router
from api.health import router as health_router

app.include_router(chat_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(health_router)
```

```python
# api/auth.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/fitbit")
async def start_auth(): ...

@router.get("/fitbit/callback")
async def auth_callback(code: str, state: str): ...
```

### トレードオフ
- **メリット**: 各ファイルが単一責務、テストが独立して書ける
- **デメリット**: ファイル数が増える（PoC では3ファイルのみ、許容範囲）

---

## PATTERN-04: Dependency Injection（モジュールレベル Singleton）

### 問題
`LangGraphAgent` と `FitbitService` は複数のリクエストで共有されるべきインスタンス。FastAPI の `Depends()` を使う方法もあるが、PoC スコープではシンプルなモジュールレベル Singleton が適切。

### 解決策
各ルーターファイルのモジュールレベルでインスタンスを1回だけ初期化する。

```python
# api/chat.py
from agent.graph import get_agent

_agent = get_agent()  # モジュールインポート時に1回だけ初期化

@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(_sse_generator(request.message, request.session_id), ...)
```

```python
# api/auth.py
from services.fitbit_service import get_fitbit_service

_service = get_fitbit_service()  # モジュールインポート時に1回だけ初期化
```

### Unit 1 との接続
`agent/graph.py` に `get_agent()` 関数を追加する:
```python
# agent/graph.py（Unit 1 の既存ファイルに追記）
_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = _build_graph()  # 既存のグラフ構築ロジック
    return _agent_instance
```

### トレードオフ
- **メリット**: シンプル、FastAPI の起動オーバーヘッドなし、Unit 1 との統合が容易
- **デメリット**: テスト時にモジュールレベルの状態を差し替えるには `monkeypatch` が必要

---

## PATTERN-05: カスタム例外 → HTTP エラー変換

### 問題
`FitbitService` のカスタム例外（`InvalidStateError` 等）をそのまま伝播させると、FastAPI が HTTP 500 として返す。

### 解決策
`AuthRouter` のエンドポイント内で `try/except` によりカスタム例外を `HTTPException` に変換する。

```python
# api/auth.py
from fastapi import HTTPException
from services.fitbit_service import InvalidStateError, StateExpiredError, TokenExchangeError

@router.get("/fitbit/callback")
async def auth_callback(code: str, state: str) -> AuthCallbackResponse:
    try:
        token = _service.exchange_code_for_token(code, state)
        return AuthCallbackResponse(
            fitbit_user_id=token.user_id,
            scope=token.scope,
        )
    except InvalidStateError:
        raise HTTPException(status_code=400, detail="invalid_state")
    except StateExpiredError:
        raise HTTPException(status_code=400, detail="state_expired")
    except TokenExchangeError as e:
        raise HTTPException(status_code=400, detail=f"token_exchange_failed: {e}")
```

### トレードオフ
- **メリット**: サービス層が FastAPI に依存しない（純粋な Python 例外）、テストが容易
- **デメリット**: 各エンドポイントで例外マッピングを書く必要がある（PoC では3種類のみ）
