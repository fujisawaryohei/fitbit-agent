# Business Rules — Unit 2: Backend API

## ルール一覧

| ID | ルール | 適用箇所 |
|---|---|---|
| BR-01 | ChatRequest バリデーション | POST /chat |
| BR-02 | SSE イベント形式 | SSE Generator |
| BR-03 | OAuth2 state 生成・検証 | GET /auth/fitbit, callback |
| BR-04 | OAuth2 スコープ | GET /auth/fitbit |
| BR-05 | CORS ポリシー | FastAPI ミドルウェア |
| BR-06 | エラーレスポンス形式 | 全エンドポイント |

---

## BR-01: ChatRequest バリデーション

| ルール | 内容 |
|---|---|
| BR-01-1 | `message` フィールドは空文字・空白のみ禁止 |
| BR-01-2 | `message` フィールドは最大 2000文字 |
| BR-01-3 | `session_id` フィールドは空文字・空白のみ禁止 |
| BR-01-4 | バリデーション失敗時は HTTP 422 Unprocessable Entity を返す（FastAPI デフォルト） |

---

## BR-02: SSE イベント形式

| ルール | 内容 |
|---|---|
| BR-02-1 | 全 SSE チャンクは `data: {JSON}\n\n` 形式で送信する |
| BR-02-2 | JSON は `SSEChunk` モデルの `model_dump_json()` で生成する |
| BR-02-3 | ストリーム完了時は必ず `type: "done"` チャンクを送信する |
| BR-02-4 | 例外発生時は `type: "error"` チャンクを送信してストリームを終了する |
| BR-02-5 | `Content-Type: text/event-stream` ヘッダーを必ず設定する |
| BR-02-6 | `Cache-Control: no-cache` ヘッダーを設定する（プロキシのバッファリング防止） |

---

## BR-03: OAuth2 state 生成・検証

| ルール | 内容 |
|---|---|
| BR-03-1 | state は `secrets.token_urlsafe(32)` で生成する（256ビット以上のランダム性） |
| BR-03-2 | state はプロセスメモリの dict に保存する（PoC スコープ） |
| BR-03-3 | callback 受信時は state が dict に存在することを確認する |
| BR-03-4 | state の有効期限は生成から 600秒（10分）とする |
| BR-03-5 | callback 処理後は state を dict から削除する（リプレイ攻撃防止） |
| BR-03-6 | state 不一致・期限切れの場合は HTTP 400 を返す |

---

## BR-04: OAuth2 スコープ

| ルール | 内容 |
|---|---|
| BR-04-1 | 必須スコープ: `activity heartrate weight nutrition` |
| BR-04-2 | スコープはスペース区切りで認可URL に付与する |
| BR-04-3 | callback で受け取ったトークンのスコープを確認し、不足スコープがある場合はエラーメッセージを返す |

---

## BR-05: CORS ポリシー

| ルール | 内容 |
|---|---|
| BR-05-1 | 開発環境では `allow_origins=["http://localhost:3000"]` を許可する |
| BR-05-2 | `allow_credentials=True` を設定する |
| BR-05-3 | `allow_methods=["*"]`, `allow_headers=["*"]` を設定する（PoC スコープ） |

---

## BR-06: エラーレスポンス形式

| ルール | 内容 |
|---|---|
| BR-06-1 | HTTP 4xx / 5xx エラーは `{"detail": "エラーメッセージ"}` 形式（FastAPI デフォルト）で返す |
| BR-06-2 | 内部エラーの詳細（スタックトレース）はレスポンスに含めない |
| BR-06-3 | SSE ストリーム内のエラーは `SSEChunk(type="error", content=...)` で返す |
