# Business Logic Model — Unit 2: Backend API

## ビジネスロジック一覧

| ID | ロジック | 説明 |
|---|---|---|
| BLM-01 | チャットSSEフロー | POST /chat を受け取り LangGraphAgent をストリーム実行してSSE送信 |
| BLM-02 | OAuth2 認可開始フロー | GET /auth/fitbit で認可URLを生成しリダイレクト |
| BLM-03 | OAuth2 コールバック処理 | GET /auth/fitbit/callback でコードをトークンに交換して保存 |
| BLM-04 | ヘルスチェック | GET /health でサービス稼働状態を返す |

---

## BLM-01: チャットSSEフロー

```
POST /chat
  │
  ├─ [1] ChatRequest バリデーション（Pydantic 自動）
  │         ├─ message: 空でない・2000文字以内
  │         └─ session_id: 空でない
  │
  ├─ [2] StreamingResponse（Content-Type: text/event-stream）を即座に返す
  │
  └─ [3] SSE Generator 実行（非同期ジェネレータ）
            │
            ├─ LangGraphAgent.stream(message, session_id) を呼び出し
            │     │
            │     └─ agent_node チャンクをイテレート
            │           │
            │           ├─ チャンク内に content あり
            │           │    └─ SSEChunk(type="chunk", content=...) を yield
            │           │
            │           └─ イテレーション完了
            │                └─ SSEChunk(type="done") を yield
            │
            └─ 例外発生時
                 └─ SSEChunk(type="error", content=エラーメッセージ) を yield
```

**実装イメージ**:
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _sse_generator(request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

async def _sse_generator(message: str, session_id: str):
    try:
        async for chunk in agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": session_id}},
        ):
            if "agent" in chunk:
                for msg in chunk["agent"]["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        data = SSEChunk(
                            type="chunk",
                            content=msg.content,
                            session_id=session_id
                        )
                        yield f"data: {data.model_dump_json()}\n\n"
        done = SSEChunk(type="done", session_id=session_id)
        yield f"data: {done.model_dump_json()}\n\n"
    except Exception as e:
        error = SSEChunk(type="error", content=str(e), session_id=session_id)
        yield f"data: {error.model_dump_json()}\n\n"
```

---

## BLM-02: OAuth2 認可開始フロー

```
GET /auth/fitbit
  │
  ├─ [1] OAuthState.generate() で state 生成
  │
  ├─ [2] state_store[state.value] = state（プロセスメモリ）
  │
  ├─ [3] FitbitClient.get_authorization_url(state.value) で認可URL構築
  │         URL例: https://www.fitbit.com/oauth2/authorize
  │               ?client_id=xxx
  │               &response_type=code
  │               &scope=activity+heartrate+weight+nutrition
  │               &redirect_uri=http://localhost:8000/auth/fitbit/callback
  │               &state=xxx
  │
  └─ [4] HTTP 302 RedirectResponse で Fitbit 認可ページへリダイレクト
```

---

## BLM-03: OAuth2 コールバック処理

```
GET /auth/fitbit/callback?code=xxx&state=yyy
  │
  ├─ [1] state パラメータ検証
  │         ├─ state_store に存在するか？ → なければ 400 Bad Request
  │         └─ is_expired() が False か？ → 期限切れなら 400 Bad Request
  │
  ├─ [2] state_store から state を削除（リプレイ攻撃防止）
  │
  ├─ [3] FitbitClient.exchange_code_for_token(code) を呼び出し
  │         POST https://api.fitbit.com/oauth2/token
  │           grant_type=authorization_code
  │           code=xxx
  │           redirect_uri=http://localhost:8000/auth/fitbit/callback
  │         → TokenResponse
  │
  ├─ [4] UserRepository.upsert(user) でトークンを DB に保存
  │         INSERT または UPDATE（fitbit_user_id が既存なら上書き）
  │         保存内容: fitbit_user_id, access_token, refresh_token,
  │                   token_expires_at (now + expires_in 秒), scope
  │
  └─ [5] AuthCallbackResponse を返す（HTTP 200 JSON）
```

**エラー時の処理**:
- Fitbit API がエラー返却 → HTTP 400 + エラーメッセージ
- state 不一致 → HTTP 400 "invalid_state"
- state 期限切れ → HTTP 400 "state_expired"

---

## BLM-04: ヘルスチェック

```
GET /health
  │
  └─ HealthResponse(status="ok") を返す（HTTP 200）
```

**設計方針**: PoC スコープではプロセス稼働確認のみ。pgvector・Fitbit API の疎通確認は含まない。
