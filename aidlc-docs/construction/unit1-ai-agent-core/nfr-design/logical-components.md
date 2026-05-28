# Logical Components — Unit 1: AI Agent Core

## コンポーネント構成図

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraphAgent                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  graph.py                                         │   │
│  │  memory_inject_node → agent_node ⇄ tool_node     │   │
│  │                            └→ memory_save_node   │   │
│  └──────────────────────────────────────────────────┘   │
│           │                    │                         │
│           ▼                    ▼                         │
│  ┌─────────────┐    ┌──────────────────────┐            │
│  │MemoryManager│    │   ToolRegistry        │            │
│  │  (manager.py)│   │  (fitbit_tools.py     │            │
│  └──────┬──────┘    │   planning_tools.py)  │            │
│         │           └──────────┬────────────┘            │
│         │                      │                         │
└─────────┼──────────────────────┼─────────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────────┐
│  EmbeddingModel │    │    FitbitClient      │
│  (Singleton)    │    │    (client.py)       │
│  e5-large       │    └────────┬────────────┘
└────────┬────────┘             │
         │                      ▼
         ▼              ┌───────────────┐
┌────────────────┐      │  Fitbit API   │
│ConnectionPool  │      │ (External)    │
│(SimplePool)    │      └───────────────┘
└────────┬───────┘
         │
         ▼
┌────────────────┐    ┌───────────────┐
│  pgvector DB   │    │  LangSmith    │
│  (Docker)      │    │  (Cloud)      │
└────────────────┘    └───────────────┘
```

---

## LC-01: EmbeddingModel（Singleton）

**ファイル**: `agent/memory/embedding.py`

| 属性 | 内容 |
|---|---|
| パターン | Singleton（遅延初期化） |
| モデル | `amazon.titan-embed-text-v2:0`（Amazon Bedrock） |
| 出力次元 | 1024 |
| リージョン | `ap-northeast-1` |
| 依存 | `langchain-aws.BedrockEmbeddings` |

> **変更履歴**: `sentence-transformers` + `intfloat/multilingual-e5-large` のローカル実行から Bedrock マネージドモデルに変更。

**インターフェース**:
```python
def embed(text: str) -> list[float]  # 1024次元 vector
```

**ライフサイクル**:
- 初回呼び出し時: `BedrockEmbeddings` インスタンスを生成してキャッシュ
- 以降: キャッシュされたインスタンスを再利用

---

## LC-02: ConnectionPool（pgvector用）

**ファイル**: `memory/connection_pool.py`

| 属性 | 内容 |
|---|---|
| パターン | Connection Pool (Singleton) |
| 実装 | `psycopg2.pool.SimpleConnectionPool` |
| minconn | 1 |
| maxconn | 5（PoC単一ユーザー想定） |
| 設定 | `PGVECTOR_DSN` 環境変数 |

**インターフェース**:
```python
def get_pool() -> SimpleConnectionPool
def get_connection() -> psycopg2.connection
def release_connection(conn: psycopg2.connection) -> None
```

**ライフサイクル**:
- 起動時: 最小接続数（1本）を確立
- 使用時: `get_connection()` で借り出し、`finally` ブロックで `release_connection()` を保証

---

## LC-03: MemoryManager

**ファイル**: `memory/manager.py`

| 属性 | 内容 |
|---|---|
| 依存 | `EmbeddingModel`、`ConnectionPool` |
| pgvector テーブル | `memories` |
| カラム | `id UUID`, `session_id TEXT`, `content TEXT`, `embedding vector(1024)`, `created_at TIMESTAMP`, `updated_at TIMESTAMP` |

**インターフェース**:
```python
def save_memory(session_id: str, content: str) -> None
def search_memories(session_id: str, query: str, limit: int = 3) -> list[str]
```

**pgvector テーブル定義**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS memories_session_id_idx ON memories(session_id);
-- コサイン類似度インデックス（PoC規模では省略可）
-- CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);
```

**類似度検索クエリ**:
```sql
SELECT content
FROM memories
WHERE session_id = %s
ORDER BY embedding <=> %s  -- コサイン距離
LIMIT %s;
```

**フォールバック動作**:
- 接続エラー / クエリエラー → `logging.error` して空リスト返却
- 会話は中断せず続行

---

## LC-04: LangSmith トレース

**設定方法**: `.env` に以下を追加するだけで LangChain/LangGraph が自動でトレースを送信

| 属性 | 内容 |
|---|---|
| パターン | 環境変数による自動トレース |
| 実装 | LangChain 組み込み（コード変更不要） |
| 設定 | `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` 環境変数 |

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=fitbit-agent
```

---

## LC-05: InMemorySaver（Short-term Memory）

**ファイル**: `agent/graph.py`（組み込み利用）

| 属性 | 内容 |
|---|---|
| 実装 | `langgraph.checkpoint.memory.InMemorySaver` |
| スコープ | プロセスライフタイム（再起動でリセット） |
| スレッド識別 | `session_id`（`thread_id` として設定） |

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

---

## 環境変数一覧（.env）

```env
# AWS 認証（EC2 インスタンスプロファイルで自動取得のため通常は不要）
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

# Fitbit（Client ID/Secret のみ。アクセストークンは Unit 2 OAuth2 フロー後に DB から取得）
FITBIT_CLIENT_ID=...
FITBIT_CLIENT_SECRET=...

# pgvector
PGVECTOR_DSN=postgresql://user:password@localhost:5432/fitbit_memory

# LangSmith（任意。LANGCHAIN_TRACING_V2=false で無効化可能）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=fitbit-agent
```

---

## ディレクトリ構成（Unit 1 コード）

```
fitbit-agent/
├── agent/
│   ├── graph.py          # LangGraph グラフ定義・コンパイル
│   ├── nodes.py          # memory_inject / agent / tool / memory_save ノード
│   ├── state.py          # AgentState (Pydantic)
│   └── langfuse_setup.py # 廃止（LangSmith は環境変数のみで設定）
├── tools/
│   ├── fitbit_tools.py   # get_steps, get_calories_burned, get_weight 等 @tool
│   └── planning_tools.py # calculate_calorie_deficit, generate_home_workout_plan 等 @tool
├── fitbit/
│   └── client.py         # FitbitClient（データ取得メソッド）
├── memory/
│   ├── manager.py        # MemoryManager
│   ├── embedding.py      # EmbeddingModel Singleton
│   └── connection_pool.py# ConnectionPool Singleton
├── main.py               # エントリポイント（Python スクリプト実行）
├── docker-compose.yml    # pgvector のみ
├── pyproject.toml
└── .env                  # 環境変数（gitignore）
```
