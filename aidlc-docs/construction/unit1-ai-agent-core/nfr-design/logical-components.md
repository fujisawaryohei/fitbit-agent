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
│  pgvector DB   │    │  LangFuse     │
│  (Docker)      │    │  (Docker)     │
└────────────────┘    └───────────────┘
```

---

## LC-01: EmbeddingModel（Singleton）

**ファイル**: `memory/embedding.py`

| 属性 | 内容 |
|---|---|
| パターン | Singleton |
| 初期化 | アプリ起動時（モジュールインポート時） |
| モデル | `intfloat/multilingual-e5-large` |
| 出力次元 | 1024 |
| 依存 | `sentence-transformers` ライブラリ |

**インターフェース**:
```python
def get_embedding_model() -> SentenceTransformer
def embed(text: str) -> list[float]  # 1024次元 normalized vector
```

**ライフサイクル**:
- 起動時: `get_embedding_model()` でモデルをロード（初回のみ560MBダウンロード）
- 以降: キャッシュされたインスタンスを返す（< 1ms）

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

## LC-04: LangFuseHandler

**ファイル**: `agent/langfuse_setup.py`

| 属性 | 内容 |
|---|---|
| パターン | Callback Delegation |
| 実装 | `langfuse.callback.CallbackHandler` |
| 設定 | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` 環境変数 |

**インターフェース**:
```python
def get_langfuse_handler() -> CallbackHandler
```

**LangGraph への統合方法**:
```python
# agent.stream() の config に渡すだけ
config = {
    "configurable": {"thread_id": session_id},
    "callbacks": [get_langfuse_handler()]
}
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
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Fitbit（Unit 1 開発時は手動設定）
FITBIT_ACCESS_TOKEN=...
FITBIT_REFRESH_TOKEN=...
FITBIT_CLIENT_ID=...
FITBIT_CLIENT_SECRET=...

# pgvector
PGVECTOR_DSN=postgresql://user:password@localhost:5432/fitbit_memory

# LangFuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

---

## ディレクトリ構成（Unit 1 コード）

```
fitbit-agent/
├── agent/
│   ├── graph.py          # LangGraph グラフ定義・コンパイル
│   ├── nodes.py          # memory_inject / agent / tool / memory_save ノード
│   ├── state.py          # AgentState (Pydantic)
│   └── langfuse_setup.py # LangFuse CallbackHandler
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
├── docker-compose.yml    # pgvector + LangFuse
├── pyproject.toml
└── .env                  # 環境変数（gitignore）
```
