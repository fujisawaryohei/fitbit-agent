# Fitbit ツール呼び出し時に「クライアントが設定されていません」エラー

## 現象

エージェントが Fitbit ツール（`get_steps` 等）を呼び出すと以下のエラーが発生する。

```
Error: Fitbit クライアントが設定されていません。先に /auth/fitbit で認証してください。
```

## 原因

`ContextVar` の sync/async コンテキスト境界の問題。

`chat()` エンドポイントは **sync 関数**のため FastAPI がスレッドプールで実行する。
そこで `set_fitbit_client()` を呼んでも、値はスレッドのコンテキストに入る。

`_sse_generator` は **async 関数**のため asyncio イベントループで実行される。
asyncio とスレッドプールはコンテキスト空間が異なるため、スレッド側でセットした値が見えない。

```
chat() [sync → スレッドプール]
  └─ set_fitbit_client()  ← スレッドのコンテキストにセット

_sse_generator [asyncio イベントループ]
  └─ _agent.astream()
       └─ get_steps ツール
            └─ get_fitbit_client()  ← asyncio のコンテキストを参照 → None！
```

## 解決

`FitbitClient` を引数として `_sse_generator` に渡し、async コンテキスト内の先頭で `set_fitbit_client()` を呼ぶ。

```python
# chat() 内
fitbit_client = FitbitClient(...)
return StreamingResponse(
    _sse_generator(message=..., session_id=..., fitbit_client=fitbit_client),
    ...
)

# _sse_generator 内（asyncio コンテキスト）
async def _sse_generator(message, session_id, fitbit_client):
    set_fitbit_client(fitbit_client)  # ← ここでセットすることで asyncio 内で共有される
    ...
```

## ポイント

Python の `ContextVar` は asyncio タスク内では継承されるが、
**sync 関数（スレッドプール）→ async 関数（イベントループ）** の境界では引き継がれない。
値をセットする場所と参照する場所が同じコンテキスト内にある必要がある。

## 対象ファイル

- `backend/controllers/chat.py`
- `agent/context.py`
