# NFR Design Patterns — Unit 1: AI Agent Core

## 適用パターン一覧

| パターン | 適用箇所 | 目的 |
|---|---|---|
| Singleton | EmbeddingModel | 起動時1回だけ初期化、全ノードで共有 |
| Connection Pool | MemoryManager ↔ pgvector | DB接続再利用、オーバーヘッド削減 |
| Null Object / Fallback | MemoryManager | メモリ取得失敗時に空リストを返し続行 |
| Error String Return | FitbitClient ツール群 | エラーをLLMへ委譲、例外を上位に伝播しない |
| Streaming Iterator | LangGraphAgent | agent.stream() でトークン単位のリアルタイム出力 |
| 環境変数トレース | LangSmith統合 | 環境変数設定のみで自動トレース、コード変更不要 |

---

## PATTERN-01: Singleton — EmbeddingModel

### 問題
`SentenceTransformer("intfloat/multilingual-e5-large")` は560MB超のモデルをロードするため、呼び出しごとに初期化すると数秒の遅延とメモリ浪費が発生する。

### 解決策
アプリ起動時に一度だけ初期化し、モジュールレベルの変数として保持する。

```python
# memory/embedding.py
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")
    return _model

def embed(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()
```

### 初期化タイミング
- `main.py` や `agent/graph.py` のモジュールインポート時に `get_embedding_model()` を呼び出してウォームアップ
- 以降の `memory_save_node` / `memory_inject_node` は即座にモデルを使用できる

### トレードオフ
- **メリット**: 初回会話から低レイテンシ、メモリ効率
- **デメリット**: 起動時間が数秒増加（PoC では許容）

---

## PATTERN-02: Connection Pool — pgvector

### 問題
`MemoryManager` の `save()` / `search()` が呼ばれるたびに新規接続を張ると、接続コストが累積する。

### 解決策
`psycopg2.pool.SimpleConnectionPool` を使い、接続を再利用する。

```python
# memory/connection_pool.py
import psycopg2.pool
import os

_pool: psycopg2.pool.SimpleConnectionPool | None = None

def get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,  # PoC: 単一ユーザーなので小さい値で十分
            dsn=os.getenv("PGVECTOR_DSN")
        )
    return _pool

def get_connection():
    return get_pool().getconn()

def release_connection(conn):
    get_pool().putconn(conn)
```

### 使用パターン（MemoryManager 内）
```python
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute(...)
    conn.commit()
finally:
    release_connection(conn)
```

### トレードオフ
- **メリット**: 接続オーバーヘッド削減、実践的なパターンの習得
- **デメリット**: 都度接続より若干コードが複雑（`minconn=1, maxconn=5` で管理）

---

## PATTERN-03: Null Object / Fallback — MemoryManager

### 問題
pgvector への接続失敗・クエリエラー時に例外を上位ノードへ伝播すると、エージェント全体が停止する。

### 解決策
エラー時は空のメモリリストを返して会話を継続する。

```python
def search_memories(session_id: str, query: str, limit: int = 3) -> list[str]:
    try:
        conn = get_connection()
        # ... pgvector クエリ実行
        return results
    except Exception as e:
        logging.error(f"Memory search failed: {e}")
        return []  # Fallback: 空リストを返す

def save_memory(session_id: str, content: str) -> None:
    try:
        # ... pgvector への保存
    except Exception as e:
        logging.error(f"Memory save failed: {e}")
        # サイレント失敗 — 会話は続行
```

---

## PATTERN-04: Error String Return — FitbitClient

### 問題
Fitbit API のエラー（401/429/404/ネットワーク障害）をPython例外として伝播させると、LangGraphのtool_nodeが停止する。

### 解決策
すべてのエラーを文字列として返し、LLMがユーザーに自然言語で伝える。

```python
def get_activities(date: str = "today") -> str | dict:
    try:
        access_token = self._get_valid_token()
        response = httpx.get(url, headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code == 200:
            return response.json()
        return f"Error {response.status_code}: {ERROR_MESSAGES.get(response.status_code, response.text)}"
    except httpx.TimeoutException:
        return "Error Network: Fitbit APIへの接続がタイムアウトしました。"
    except Exception as e:
        return f"Error: {str(e)}"
```

---

## PATTERN-05: Streaming Iterator — LangGraphAgent

### 問題
LLMの全応答を待ってから返すと、ユーザーは長い沈黙を経験する。

### 解決策
`agent.stream()` でチャンクをイテレートし、`agent_node` からのトークンをリアルタイム出力する。

```python
# Unit 1: Python スクリプト実行時（ターミナル出力）
for chunk in agent.stream(
    {"messages": [HumanMessage(content=user_input)]},
    config={
        "configurable": {"thread_id": session_id},
    }
):
    if "agent" in chunk:
        for msg in chunk["agent"]["messages"]:
            if hasattr(msg, "content") and msg.content:
                print(msg.content, end="", flush=True)
print()  # 改行
```

### Unit 2 以降への拡張
- Unit 2 では FastAPI の `StreamingResponse` + SSE に置き換える
- `agent.stream()` 自体は変更不要、出力先のみ変わる

---

## PATTERN-06: 環境変数トレース — LangSmith

### 問題
LLMトレースのロジックをノードのビジネスロジックと混在させると、コードが複雑になる。

### 解決策
`.env` に環境変数を設定するだけで、LangChain/LangGraph が自動でトレースを LangSmith に送信する。コード変更不要。

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=fitbit-agent
```

### 効果
- ノード・ツールの全実行ログが LangSmith ダッシュボード（https://smith.langchain.com）に自動記録
- ビジネスロジックコードへの変更なし
- Docker サービスの追加不要
