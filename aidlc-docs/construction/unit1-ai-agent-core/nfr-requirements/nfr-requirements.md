# NFR Requirements — Unit 1: AI Agent Core

## 対象スコープ
Unit 1: AI Agent Core（LangGraph グラフ・ツール・FitbitClient・MemoryManager）

---

## NFR-01: パフォーマンス

| ID | 要件 | 値 | 備考 |
|---|---|---|---|
| NFR-01-1 | LLM 応答レイテンシ（初回トークン） | < 3秒 | PoC レベル目標 |
| NFR-01-2 | ストリーミングレスポンス方式 | `agent.stream()` | トークン単位でリアルタイム出力 |
| NFR-01-3 | Fitbit API レスポンスタイム | < 2秒 | Fitbit API SLA 依存 |
| NFR-01-4 | pgvector 類似検索（top-3） | < 500ms | 小規模データのため問題なし |
| NFR-01-5 | 埋め込みモデル初回ロード | < 30秒 | モデルキャッシュ後は < 1秒 |

---

## NFR-02: スケーラビリティ

| ID | 要件 | 値 | 備考 |
|---|---|---|---|
| NFR-02-1 | 同時接続ユーザー数 | 1人（PoC） | Unit 1 は個人学習用途 |
| NFR-02-2 | セッション数 | 制限なし（開発中） | MemorySaver はインメモリのみ |
| NFR-02-3 | pgvector レコード数 | 〜1,000件以下（PoC） | ベクトルインデックス不要 |

---

## NFR-03: 信頼性・エラー処理

| ID | 要件 | 内容 |
|---|---|---|
| NFR-03-1 | Fitbit API エラー | エラー文字列をツール戻り値として返却、LLM がユーザーへ通知 |
| NFR-03-2 | LLM API エラー | LangChain の組み込みリトライを使用（デフォルト設定） |
| NFR-03-3 | pgvector 接続エラー | エラーログ出力後、MemoryManager は空のメモリを返して続行 |
| NFR-03-4 | 埋め込みモデルエラー | エラーログ出力後、Long-term memory なしで会話を続行 |
| NFR-03-5 | トークン切れ | `_get_valid_token` が自動リフレッシュ、失敗時はエラー文字列返却 |

---

## NFR-04: 観測性（Observability）

| ID | 要件 | 内容 |
|---|---|---|
| NFR-04-1 | LLM トレース | LangFuse（Docker セルフホスト）で全ノード・ツール呼び出しを記録 |
| NFR-04-2 | ログレベル | 開発中は `DEBUG`、ターミナル出力 |
| NFR-04-3 | エラーログ | Python `logging` モジュール、標準エラー出力 |
| NFR-04-4 | LangFuse ダッシュボード | `http://localhost:3000` でトレースを確認 |

---

## NFR-05: セキュリティ（PoC スコープ）

| ID | 要件 | 内容 |
|---|---|---|
| NFR-05-1 | Fitbit トークン | `.env` ファイルに保存（Unit 1 開発時のみ、gitignore 必須） |
| NFR-05-2 | API キー管理 | Anthropic API キー・LangFuse キーも `.env` で管理 |
| NFR-05-3 | pgvector 接続情報 | `.env` で管理（ハードコード禁止） |

> **注**: Security Extension は無効（PoC スコープ）。本番化時は見直しが必要。

---

## NFR-06: メモリ仕様

| ID | 要件 | 内容 |
|---|---|---|
| NFR-06-1 | Short-term memory | LangGraph `InMemorySaver`（プロセス再起動でリセット） |
| NFR-06-2 | Long-term memory | PostgreSQL + pgvector（Docker コンテナ） |
| NFR-06-3 | 埋め込みベクトル次元数 | **1024次元**（multilingual-e5-large） |
| NFR-06-4 | pgvector カラム型 | `vector(1024)` |
| NFR-06-5 | 類似度計算方式 | コサイン類似度（`<=>` 演算子） |

---

## NFR-07: 開発・テスト要件

| ID | 要件 | 内容 |
|---|---|---|
| NFR-07-1 | 単体実行 | FastAPI なしで Python スクリプトとして実行可能 |
| NFR-07-2 | テストカバレッジ | 80%以上（Pytest + Hypothesis による PBT） |
| NFR-07-3 | 型チェック | `mypy` または `pyright` を使用 |
| NFR-07-4 | linting | `ruff` を使用 |
