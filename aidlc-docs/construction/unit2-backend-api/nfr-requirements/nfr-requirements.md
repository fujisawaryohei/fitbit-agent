# NFR Requirements — Unit 2: Backend API

## 対象スコープ
Unit 2: Backend API（FastAPI・SSE・OAuth2フロー・LangGraphAgent統合）

---

## NFR-01: パフォーマンス

| ID | 要件 | 値 | 備考 |
|---|---|---|---|
| NFR-01-1 | POST /chat SSE 初回チャンク到達時間 | < 3秒 | LLM 初回トークンレイテンシに依存 |
| NFR-01-2 | SSE チャンク送信間隔 | LLM 生成速度に依存 | バッファリングなしでリアルタイム送信 |
| NFR-01-3 | GET /health レスポンスタイム | < 100ms | 外部依存なし |
| NFR-01-4 | GET /auth/fitbit レスポンスタイム | < 200ms | state 生成 + リダイレクトのみ |
| NFR-01-5 | GET /auth/fitbit/callback レスポンスタイム | < 3秒 | Fitbit トークン交換 API 依存 |

---

## NFR-02: スケーラビリティ

| ID | 要件 | 値 | 備考 |
|---|---|---|---|
| NFR-02-1 | 同時接続ユーザー数 | 1人（PoC） | 個人学習用途 |
| NFR-02-2 | SSE セッション数 | 1セッション（PoC） | プロセスメモリの LangGraph InMemorySaver 制約 |
| NFR-02-3 | OAuth2 state 保持数 | 〜10件以下（PoC） | プロセスメモリのため制限なし（実質小数） |

---

## NFR-03: 信頼性・エラー処理

| ID | 要件 | 内容 |
|---|---|---|
| NFR-03-1 | LangGraphAgent エラー | SSEChunk(type="error") でクライアントに通知し、ストリームを正常終了させる |
| NFR-03-2 | Fitbit API トークン切れ（401） | FitbitClient が自動リフレッシュ（Unit 1 の既存実装）、失敗時は SSE error チャンク送信 |
| NFR-03-3 | OAuth2 state 不一致 | HTTP 400 + `{"detail": "invalid_state"}` |
| NFR-03-4 | OAuth2 state 期限切れ | HTTP 400 + `{"detail": "state_expired"}` |
| NFR-03-5 | Fitbit トークン交換エラー | HTTP 400 + `{"detail": "token_exchange_failed: <message>"}` |
| NFR-03-6 | FastAPI 未処理例外 | HTTP 500（FastAPI デフォルト）、詳細はサーバーログのみ |
| NFR-03-7 | クライアント接続切断時の SSE | Python の `asyncio.CancelledError` を適切にハンドリングして後処理を実行 |

---

## NFR-04: 観測性（Observability）

| ID | 要件 | 内容 |
|---|---|---|
| NFR-04-1 | API アクセスログ | uvicorn のデフォルトアクセスログ（標準出力） |
| NFR-04-2 | LLM トレース | LangSmith（Unit 1 から継続、環境変数のみで設定） |
| NFR-04-3 | エラーログ | Python `logging` モジュール、標準エラー出力 |
| NFR-04-4 | ログレベル | 開発中は `DEBUG` |

---

## NFR-05: セキュリティ（PoC スコープ）

| ID | 要件 | 内容 |
|---|---|---|
| NFR-05-1 | OAuth2 CSRF防止 | state パラメータで検証（BR-03 参照） |
| NFR-05-2 | トークン保管 | アクセストークン・リフレッシュトークンは `.env` で管理（gitignore 必須） |
| NFR-05-3 | CORS | `localhost:3000` のみ許可（BR-05 参照） |
| NFR-05-4 | 認証・認可 | PoC スコープのため API 認証なし（将来: API Key or JWT） |
| NFR-05-5 | レート制限 | PoC スコープのため未実装（将来: slowapi 等で追加） |

> **注**: Security Extension は無効（PoC スコープ）。本番化時は API 認証・レート制限・HTTPS 必須。

---

## NFR-06: 開発・テスト要件

| ID | 要件 | 内容 |
|---|---|---|
| NFR-06-1 | ローカル起動 | `uvicorn main:app --reload` で起動可能 |
| NFR-06-2 | 動作確認 | `curl` / `httpx` / Postman で各エンドポイントをテスト |
| NFR-06-3 | テストカバレッジ | 80%以上（pytest + pytest-asyncio） |
| NFR-06-4 | 非同期テスト | `pytest-asyncio` + `httpx.AsyncClient` で FastAPI エンドポイントを非同期テスト |
| NFR-06-5 | SSE テスト | `httpx.AsyncClient` の `stream()` コンテキストで SSE チャンクを受信・検証 |
| NFR-06-6 | LangGraphAgent モック | テスト時は `agent.astream()` をモックして SSE ロジックのみをテスト |
