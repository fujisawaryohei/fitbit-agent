# Component Dependency — Fitbit Weight Management AI Agent

## 依存関係マトリクス

| コンポーネント | 依存先 | 通信方式 |
|--------------|--------|---------|
| `ChatUI` | `FastAPIApp` | HTTP (POST /chat → SSE), HTTP (GET /auth/*) |
| `FastAPIApp` | `LangGraphAgent` | 直接呼び出し（同一プロセス） |
| `FastAPIApp` | `FitbitService` | 直接呼び出し（同一プロセス） |
| `LangGraphAgent` | `ToolRegistry` | 直接呼び出し（LangGraph tool_node） |
| `LangGraphAgent` | `MemoryManager` | 直接呼び出し（memory_inject_node / memory_save_node） |
| `LangGraphAgent` | LLM API (Claude) | HTTPS（Anthropic API） |
| `ToolRegistry` | `FitbitClient` | 直接呼び出し（同一プロセス） |
| `FitbitClient` | Fitbit API | HTTPS（外部API） |
| `MemoryManager` | `VectorStore` (pgvector) | TCP（PostgreSQL接続） |

---

## データフロー図

```
[ブラウザ]
    |
    | HTTP POST /chat  (message, session_id)
    v
[ChatUI: Next.js]
    |
    | fetch + ReadableStream (SSE)
    v
[FastAPIApp: POST /chat]
    |
    | agent.stream(message, session_id)
    v
[LangGraphAgent]
    |
    +--[memory_inject_node]---> [MemoryManager] ---> [pgvector DB]
    |                           （Long-term memory 検索）
    |
    +--[agent_node] ----------> [LLM API: Claude]
    |   （ツール呼び出し判断）
    |
    +--[tool_node] -----------> [ToolRegistry @tool]
    |   （Fitbit / 計算）             |
    |                                 v
    |                           [FitbitClient] ---> [Fitbit API]
    |
    +--[memory_save_node] ----> [MemoryManager] ---> [pgvector DB]
        （重要情報の保存）
    |
    | SSE chunks (text/event-stream)
    v
[ChatUI: Next.js]
    |
    | リアルタイム表示
    v
[ブラウザ]

---

[ブラウザ]
    |
    | GET /auth/fitbit
    v
[FastAPIApp]
    |
    | fitbit_service.get_authorization_url()
    v
[FitbitService] --> [FitbitClient.get_authorization_url()]
    |
    | 302 Redirect
    v
[Fitbit 認証ページ]
    |
    | GET /auth/fitbit/callback?code=xxx
    v
[FastAPIApp] --> [FitbitService.handle_callback(code)]
                      --> [FitbitClient.exchange_code_for_token(code)]
                      --> トークン保存
```

---

## コンポーネント配置図

```
+------------------------------------------+
|  ブラウザ                                  |
|  +------------------------------------+   |
|  |  ChatUI (Next.js + TypeScript)     |   |
|  |  - チャット画面                     |   |
|  |  - SSE クライアント                 |   |
|  |  - Fitbit 接続ステータス            |   |
|  +------------------------------------+   |
+------------------------------------------+
              | HTTP / SSE
              v
+------------------------------------------+
|  Backend (Python / 同一プロセス)           |
|                                          |
|  +----------------+                     |
|  | FastAPIApp     |                     |
|  | POST /chat     |                     |
|  | GET /auth/*    |                     |
|  +----------------+                     |
|       |          |                      |
|       v          v                      |
|  +-----------+  +---------------+       |
|  |LangGraph  |  | FitbitService |       |
|  |Agent      |  +---------------+       |
|  |           |        |                 |
|  | [nodes]   |  +-----v------+         |
|  |           |  |FitbitClient|         |
|  +-----------+  +------------+         |
|       |    |                           |
|       |    +----> ToolRegistry         |
|       |               |                |
|       v               v                |
|  MemoryManager   FitbitClient          |
+-----|-----------------------------------+
      |                |
      v                v
+----------+    +------------------+
| pgvector |    | Fitbit API       |
| (Docker) |    | (外部HTTPS)      |
+----------+    +------------------+

+------------------+
| LLM API (Claude) |
| (外部HTTPS)      |
+------------------+
```
