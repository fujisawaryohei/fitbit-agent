# SSE（Server-Sent Events）実装メモ

## 全体構造

```
StreamingResponse
    └── async for chunk in _sse_generator     # SSE チャンクをイテレート
            └── async for chunk in _agent.astream  # LLM チャンクをイテレート
                    └── for msg in chunk["agent"]["messages"]
                            └── yield → StreamingResponse へ
```

---

## 責務の分離

| クラス/関数 | 責務 |
|---|---|
| `StreamingResponse` | HTTP ヘッダー設定・TCP 接続確立・ジェネレータのイテレート・接続クローズ |
| `_sse_generator` | LLM からデータ取得・SSE フォーマット変換・yield |

`StreamingResponse` は「器」。**何を流すか**は渡されたジェネレータが決める。

---

## ジェネレータとは

`yield` を含む関数はすべてジェネレータ関数。

```python
def gen():
    yield 1   # 値を返して一時停止
    yield 2   # 再開して値を返して一時停止
```

- 呼び出してもすぐ実行されず、**ジェネレータオブジェクト**が返る
- `next()` または `for` でイテレートされたタイミングで実行される
- `yield` のたびに状態を保持して停止し、次の `next()` で再開する

---

## 非同期ジェネレータ

`async def` + `yield` の組み合わせ。内部で `await` が使える。

```python
async def _sse_generator(message, session_id):
    async for chunk in _agent.astream(...):  # await を使うため async def が必要
        yield f"data: ...\n\n"
```

| | 同期 | 非同期 |
|---|---|---|
| 定義 | `def` + `yield` | `async def` + `yield` |
| 次の値を取得 | `next(gen)` | `await gen.__anext__()` |
| ループ構文 | `for` | `async for` |
| 終了シグナル | `StopIteration` | `StopAsyncIteration` |

---

## SSE フォーマット

SSE はテキストプロトコルのため、Python オブジェクトをそのまま送れない。
`model_dump_json()` で JSON 文字列に変換してから送信する。

```
data: {"type":"chunk","content":"こんにちは","session_id":"abc"}\n\n
data: {"type":"chunk","content":"！","session_id":"abc"}\n\n
data: {"type":"done","content":"","session_id":"abc"}\n\n
```

---

## type フィールドの役割

| type      | 意味　　　　　 | フロントエンドの処理　　　 |
| -----------| ----------------| ----------------------------|
| `"chunk"` | LLM のトークン | テキストを追記表示　　　　 |
| `"done"`  | ストリーム完了 | スピナー停止・入力欄を再開 |
| `"error"` | エラー発生　　 | エラーメッセージを表示　　 |

`type:"done"` はアプリレベルの終了通知。HTTP レベルの接続クローズは非同期ジェネレータの終了を `StreamingResponse` が検知して行う。

---

## TCP 接続のライフサイクル

```
非同期ジェネレータ終了（関数の末尾に到達）
    → StopAsyncIteration 発生
    → StreamingResponse が検知
    → HTTP ボディ終端（チャンク転送エンコーディングの 0\r\n\r\n）を送信
    → TCP 接続クローズ
```
