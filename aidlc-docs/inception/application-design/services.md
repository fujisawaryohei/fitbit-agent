# Services — Fitbit Weight Management AI Agent

## サービス一覧

| サービス | 責務 | 主な依存関係 |
|---------|------|------------|
| `FitbitService` | Fitbit OAuth2フロー・FitbitClientのライフサイクル管理 | FitbitClient |
| `MemoryService` | Short/Long-term メモリの統合管理 | MemoryManager, VectorStore |

> **Note**: `AgentService` 抽象層は設けない。`FastAPIApp` が `LangGraphAgent` を直接使用する。

---

## LangGraphAgent（FastAPIApp から直接利用）

**役割**: FastAPI のエンドポイントから直接インスタンス化・呼び出しを行う。

**初期化（アプリ起動時）**:
```python
# main.py (FastAPI)
agent = LangGraphAgent(
    llm=ChatAnthropic(model="claude-sonnet-4-6"),
    tools=build_tools(fitbit_client),   # ToolRegistry
    memory_manager=memory_manager,      # MemoryManager
    checkpointer=MemorySaver(),         # Short-term memory
)
```

**チャットフロー（`POST /chat` 呼び出し時）**:
```
1. memory_inject_node : Long-term memory を検索 → コンテキスト注入
2. agent_node         : LLM でツール使用判断
3. [tool_calls あり]
   └─ tool_node       : @tool を実行（Fitbit API / プランニング計算）
   └─ agent_node      : ループ（ツール結果を受けて再思考）
4. [tool_calls なし]
   └─ memory_save_node: 重要情報を Long-term memory に保存
5. SSE チャンクをストリーム送信
```

---

## FitbitService

**役割**: Fitbit OAuth2フロー全体と `FitbitClient` のライフサイクル管理。

**認証開始フロー**:
```
1. FitbitClient.get_authorization_url() で認証URL生成
2. state（CSRF対策トークン）をサーバー側で一時保持
3. ユーザーを Fitbit 認証ページへリダイレクト
```

**コールバック処理フロー**:
```
1. state 検証（CSRF対策）
2. FitbitClient.exchange_code_for_token(code) でトークン取得
3. TokenData を .env / ローカルファイルに保存
4. FitbitClient のインスタンスにトークンをセット
5. 認証完了レスポンスを返す
```

**ToolRegistry への FitbitClient 提供**:
- `FitbitService` が管理する `FitbitClient` のシングルトンインスタンスをツールに注入
- トークンリフレッシュは `FitbitClient._get_valid_token()` が自動処理

---

## MemoryService

**役割**: Short-term / Long-term メモリの統合管理。

**Short-term memory（MemorySaver）**:
- LangGraph の `MemorySaver` チェックポインタが自動管理
- `session_id`（= `thread_id`）をキーに会話履歴を保持
- `LangGraphAgent` 内部で透過的に動作

**Long-term memory（pgvector）**:
- `MemoryManager` を通じて操作
- **保存タイミング**: `memory_save_node`（各会話ターン終了前）
- **検索タイミング**: `memory_inject_node`（各会話ターン開始前）

**保存するメモリカテゴリ**:

| カテゴリ | 例 |
|---------|-----|
| 目標情報 | 目標体重58kg・3ヶ月で達成 |
| 食事の好み | 炭水化物少なめが好き |
| 運動の好み | 朝15分程度が理想 |
| 過去のプランサマリー | 2026-05 作成プランの概要 |

**PostgreSQL + pgvector ローカル起動**:
- Docker Compose で `pgvector/pgvector:pg16` イメージを使用
- 接続: `asyncpg` または `psycopg2`
