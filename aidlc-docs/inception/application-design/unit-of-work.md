# Unit of Work — Fitbit Weight Management AI Agent

## 分割方針

- **ユニット数**: 3
- **実装順序**: Unit 1 → Unit 2 → Unit 3
- **デバッグ方針**: 各ユニットを print / ログで動作確認しながら段階的に実装
- **観測ツール**: LangFuse（Docker セルフホスト）でエージェントのトレースを可視化

---

## Unit 1: AI Agent Core

**実装順序**: 第1位（最初に実装）

### 責務
- LangGraph カスタム ReAct グラフの実装（ノード・エッジ・条件分岐を手動定義）
- 8本の LangGraph ツール（@tool）の実装
- **FitbitClient（データ取得メソッド）の実装** — ツールがFitbit APIを呼び出すために必須
- Short-term memory（LangGraph MemorySaver）の組み込み
- Long-term memory（PostgreSQL + pgvector）の実装
- LangFuse による LLM トレース・デバッグ観測の組み込み

### 含まれるコンポーネント
- `LangGraphAgent`（graph.py / nodes.py / state.py）
- `ToolRegistry`（fitbit_tools.py / planning_tools.py）
- **`FitbitClient`（fitbit/client.py）— データ取得メソッド群**
- `MemoryManager`（memory/manager.py）
- `VectorStore`（pgvector）

> **FitbitClient の役割分担**:
> - Unit 1 で実装: `get_activities()`, `get_body_data()`, `get_heart_rate()`, `get_food_log()` など**データ取得メソッド**
> - Unit 2 で実装: `get_authorization_url()`, `exchange_code_for_token()`, `refresh_access_token()` など **OAuth2フロー**
> - 同一クラス内に共存する。Unit 1 開発時はトークンを `.env` に手動設定して動作確認する

### 観測ツール: LangFuse（Docker セルフホスト）
- `docker-compose.yml` に LangFuse サービスを追加
- Python: `langfuse` SDK + `CallbackHandler` を LangChain/LangGraph に組み込む
- エージェントの各ノード実行・ツール呼び出し・LLM応答をトレースとして記録
- ブラウザで `http://localhost:3000` からトレースを確認しながらデバッグ

```python
# LangFuse トレース組み込みイメージ
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key="...",
    secret_key="...",
    host="http://localhost:3000"
)

# LangGraph 実行時に callback として渡す
agent.stream(input, config={"callbacks": [langfuse_handler]})
```

### 開発検証方法（print デバッグ）
- FastAPI なしで Python スクリプトとして単体実行
- `agent.stream()` の出力をターミナルで print 確認
- LangFuse ダッシュボードでトレースを可視化

---

## Unit 2: Backend API

**実装順序**: 第2位（Unit 1 の動作確認後）

### 責務
- FastAPI エンドポイントの実装（POST /chat, GET /auth/fitbit*, GET /health）
- SSE（Server-Sent Events）ストリーミングレスポンスの実装
- **FitbitClient への OAuth2 フローメソッドの追加**（Unit 1 で実装済みのクラスに追記）
- FitbitService による OAuth2 フロー管理
- Unit 1 の LangGraphAgent を呼び出す API レイヤーの組み込み

### 含まれるコンポーネント
- `FastAPIApp`（main.py / api/chat.py / api/auth.py）
- **`FitbitClient` への追記**（OAuth2メソッド: `get_authorization_url`, `exchange_code_for_token`, `refresh_access_token`）
- `FitbitService`（services/fitbit_service.py）

### 開発検証方法
- `uvicorn` でローカル起動
- `curl` / `httpx` / Postman で各エンドポイントを手動テスト
- LangFuse でエンドポイント経由のエージェントトレースを確認

---

## Unit 3: Frontend

**実装順序**: 第3位（Unit 2 の API 動作確認後）

### 責務
- Next.js + TypeScript によるチャット UI の実装
- SSE クライアントの実装（FastAPI からのストリーミング受信・リアルタイム表示）
- Fitbit 接続ステータスの表示（接続済み / 未接続）
- Fitbit 認証フロー開始ボタン

### 含まれるコンポーネント
- `ChatUI`（frontend/app/page.tsx / components/Chat.tsx）

### 開発検証方法
- `npm run dev` でローカル起動（`localhost:3000`）
- ブラウザで実際にチャットを送信して Unit 2 API との連携を確認

---

## 技術スタック補足（LangFuse 追加）

| 用途 | 技術 |
|------|------|
| LLM観測・トレース | LangFuse（Docker セルフホスト） |
| LangFuse DB | PostgreSQL（LangFuse 専用、pgvector 用とは別コンテナ） |

### docker-compose.yml 構成（想定）

```yaml
services:
  # Long-term memory 用
  pgvector:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]

  # LangFuse セルフホスト
  langfuse-server:
    image: langfuse/langfuse:latest
    ports: ["3000:3000"]
    depends_on: [langfuse-db]

  langfuse-db:
    image: postgres:16
    # LangFuse 専用 DB
```
