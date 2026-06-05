# Application Design — Fitbit Weight Management AI Agent

## 概要

Fitbit APIから取得した健康データをもとに、カスタム ReAct エージェント（LangGraph）が目標体重達成プランを提案するフルスタックチャットアプリケーションの設計。

---

## テクノロジースタック（確定）

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js / TypeScript |
| バックエンド API | FastAPI (Python) |
| AI エージェント | LangGraph カスタムグラフ（ReAct手動実装） |
| LLM | Claude Haiku (Amazon Bedrock) — `jp.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Embeddings | Amazon Titan Embed Text v2 (Bedrock) |
| Short-term memory | LangGraph MemorySaver（in-context） |
| Long-term memory | PostgreSQL + pgvector（セマンティックメモリ） |
| ストリーミング | SSE（Server-Sent Events） |
| Fitbit 認証 | OAuth2 Authorization Code Flow |
| Fitbit クライアント | FitbitClient クラス（Python） |
| DI | dependency-injector（DIコンテナ） |
| 型チェック | mypy |
| Lint / Format | ruff |
| DB（ローカル） | Docker Compose（pgvector/pgvector:pg16） |

---

## コンポーネント構成

詳細: [`components.md`](./components.md)

| コンポーネント | レイヤー | 主責務 |
|--------------|---------|-------|
| `ChatUI` | Frontend | チャット画面・SSE受信 |
| `FastAPIApp` | Backend | エンドポイント・ルーティング |
| `LangGraphAgent` | AI Agent | カスタムReActグラフ・メモリ統合 |
| `FitbitClient` | Integration | OAuth2・API呼び出し |
| `ToolRegistry` | AI Agent | @tool 定義（8ツール） |
| `MemoryManager` | Memory | Short/Long-term メモリ統合 |
| `VectorStore` | Memory | pgvector 永続化・検索 |

---

## LangGraph グラフ構造

```
[START]
  └─→ memory_inject_node   ← Long-term memory 検索・コンテキスト注入
        └─→ agent_node     ← LLM 呼び出し（Claude）
              ├─→ tool_node          (tool_calls あり)
              │     └─→ agent_node  （ReActループ）
              └─→ memory_save_node  (tool_calls なし → END前)
                    └─→ [END]
```

---

## ToolRegistry — 定義ツール一覧

詳細: [`component-methods.md`](./component-methods.md)

| ツール | 対応US | 概要 |
|-------|--------|------|
| `get_steps` | US-04 | 歩数取得 |
| `get_calories_burned` | US-04 | 消費カロリー取得 |
| `get_weight` | US-05 | 体重・BMI取得 |
| `get_heart_rate` | US-06 | 心拍数取得 |
| `get_calories_in` | US-07 | 摂取カロリー取得 |
| `calculate_calorie_deficit` | US-10 | カロリー赤字計算 |
| `generate_home_workout_plan` | US-12 | 自宅運動プラン生成 |
| `get_weekly_progress` | US-13 | 週次進捗集計 |

---

## サービス設計

詳細: [`services.md`](./services.md)

- **LangGraphAgent**: FastAPI から直接呼び出し（同一プロセス・疎結合なし）
- **FitbitService**: OAuth2フロー管理・FitbitClient ライフサイクル管理
- **MemoryService**: MemorySaver（Short-term）+ pgvector（Long-term）の統合

---

## 依存関係・データフロー

詳細: [`component-dependency.md`](./component-dependency.md)

```
ChatUI → FastAPIApp → LangGraphAgent → ToolRegistry → FitbitClient → Fitbit API
                                     → MemoryManager → pgvector
                                     → LLM API (Claude)
```

---

## ディレクトリ構成（実装済み）

```
fitbit-agent/
├── server.py                          # FastAPI アプリ起動エントリポイント
├── pyproject.toml                     # 依存管理・mypy/ruff 設定
├── .env / .env.sample                 # 環境変数
│
├── frontend/                          # Next.js + TypeScript
│   ├── next.config.ts                 # リライト設定（BACKEND_URL 等の環境変数参照）
│   ├── .env / .env.sample             # フロントエンド専用環境変数
│   └── src/
│       ├── app/
│       │   ├── page.tsx               # チャット画面
│       │   ├── chat/[chat_id]/page.tsx
│       │   └── api/chat/route.ts      # SSE プロキシ（Route Handler）
│       ├── components/
│       │   ├── Chat.tsx
│       │   ├── ChatHistory.tsx
│       │   ├── FitbitStatus.tsx
│       │   └── ...
│       └── lib/api.ts
│
├── backend/                           # FastAPI バックエンド
│   ├── containers.py                  # DIコンテナ（dependency-injector）
│   ├── router.py                      # ルーター集約
│   ├── controllers/
│   │   ├── auth.py                    # GET /auth/fitbit*
│   │   └── chat.py                    # POST /chat, GET /chats, GET /chats/{id}/messages
│   ├── decorators/
│   │   └── masked_credentials.py      # ログマスクデコレーター
│   ├── services/
│   │   └── fitbit_service.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── chat_repository.py
│   │   └── message_repository.py
│   ├── models/
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── message.py
│   │   └── ...
│   ├── schemas/
│   │   └── chat.py                    # ChatRequest, SSEChunk, ChatSummaryResponse 等
│   ├── config/
│   │   └── connection_pool.py
│   └── migrations/                    # Alembic
│
├── agent/                             # LangGraph エージェント
│   ├── graph.py
│   ├── nodes.py
│   ├── state.py
│   ├── context.py
│   ├── fitbit/client.py
│   ├── memory/
│   │   ├── manager.py
│   │   └── embedding.py
│   └── tools/
│       ├── fitbit_tools.py
│       └── planning_tools.py
│
└── docker-compose.yml
```
