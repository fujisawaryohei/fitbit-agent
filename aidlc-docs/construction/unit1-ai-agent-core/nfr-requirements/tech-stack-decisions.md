# Tech Stack Decisions — Unit 1: AI Agent Core

## 言語・ランタイム

| 技術 | バージョン | 選定理由 |
|---|---|---|
| Python | 3.11 | LangGraph・LangChain の安定サポートバージョン |
| uv | latest | 高速パッケージ管理（pip の代替） |

---

## AI / LLM フレームワーク

| 技術 | バージョン | 選定理由 |
|---|---|---|
| LangGraph | 0.2.x | カスタム ReAct グラフの手動実装に最適 |
| LangChain Core | 0.3.x | LangGraph の依存ライブラリ |
| langchain-anthropic | latest | Claude API へのアクセス |
| LLM モデル | `claude-sonnet-4-6` | 最新 Claude モデル、高いコーディング能力 |

---

## 埋め込みモデル（Long-term memory 用）

| 技術 | 値 | 選定理由 |
|---|---|---|
| モデル名 | `intfloat/multilingual-e5-large` | ローカル実行・無料・日本語対応・高品質 |
| ライブラリ | `sentence-transformers` | Hugging Face モデルのローカル実行 |
| ベクトル次元数 | **1024** | multilingual-e5-large の出力次元 |
| 実行環境 | ローカル CPU（PoC）| GPU 不要、モデルは初回起動時に自動ダウンロード |

```python
# 使用イメージ
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-large")
embedding = model.encode("テキスト", normalize_embeddings=True).tolist()
# → 1024次元の float list
```

---

## メモリ

| 技術 | 選定内容 | 備考 |
|---|---|---|
| Short-term memory | `langgraph.checkpoint.memory.InMemorySaver` | プロセス再起動でリセット（Unit 1 開発用途） |
| Long-term memory DB | PostgreSQL + pgvector（Docker） | `pgvector/pgvector:pg16` イメージ |
| pgvector カラム | `vector(1024)` | multilingual-e5-large の次元数 |

---

## エージェントレスポンス

| 技術 | 選定内容 | 備考 |
|---|---|---|
| 実行方式 | `agent.stream()` | トークン単位のストリーミング出力 |
| Unit 1 出力先 | ターミナル（stdout） | FastAPI なし、Python スクリプトで直接実行 |
| Unit 2 以降 | SSE（Server-Sent Events） | FastAPI 経由でフロントエンドへストリーミング |

```python
# Unit 1 でのストリーミング実行イメージ
for chunk in agent.stream(
    {"messages": [HumanMessage(content=user_input)]},
    config={"configurable": {"thread_id": session_id}, 
            "callbacks": [langfuse_handler]}
):
    if "agent" in chunk:
        for msg in chunk["agent"]["messages"]:
            print(msg.content, end="", flush=True)
```

---

## 観測・トレース

| 技術 | バージョン | 備考 |
|---|---|---|
| LangFuse | Docker セルフホスト（latest） | `http://localhost:3000` |
| langfuse SDK | `langfuse` (Python) | `CallbackHandler` で LangGraph に統合 |
| LangFuse DB | PostgreSQL（専用コンテナ） | pgvector 用とは別インスタンス |

---

## データベース（Docker Compose）

| サービス | イメージ | ポート | 用途 |
|---|---|---|---|
| pgvector | `pgvector/pgvector:pg16` | 5432 | Long-term memory |
| langfuse-server | `langfuse/langfuse:latest` | 3000 | LLM トレース UI |
| langfuse-db | `postgres:16` | 5433 | LangFuse 専用 DB |

---

## コード品質ツール

| ツール | 用途 |
|---|---|
| `ruff` | linting・フォーマット |
| `mypy` | 静的型チェック |
| `pytest` | ユニットテスト・統合テスト |
| `hypothesis` | Property-Based Testing（PBT） |

---

## 依存ライブラリまとめ（pyproject.toml イメージ）

```toml
[project]
requires-python = ">=3.11"

dependencies = [
    # AI / LangGraph
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "langfuse>=2.0.0",

    # Embedding
    "sentence-transformers>=3.0.0",

    # DB
    "psycopg2-binary>=2.9.0",
    "pgvector>=0.3.0",

    # Utils
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "hypothesis>=6.0.0",
    "mypy>=1.10.0",
    "ruff>=0.5.0",
]
```
