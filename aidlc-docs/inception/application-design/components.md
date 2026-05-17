# Components — Fitbit Weight Management AI Agent

## コンポーネント一覧

| コンポーネント | レイヤー | 言語/FW | 責務概要 |
|--------------|---------|---------|---------|
| `ChatUI` | Frontend | Next.js + TypeScript | チャット画面・SSE受信・Fitbit接続状態表示 |
| `FastAPIApp` | Backend | FastAPI (Python) | HTTPエンドポイント・ルーティング・CORS |
| `LangGraphAgent` | AI Agent | LangGraph (Python) | カスタムReActグラフ・ツール呼び出し・メモリ統合 |
| `FitbitClient` | Integration | Python | OAuth2認証・トークン管理・Fitbit APIリクエスト |
| `ToolRegistry` | AI Agent | LangChain @tool | LangGraph に登録する全ツールの定義 |
| `MemoryManager` | Memory | Python | Short-term/Long-term メモリの統合管理 |
| `VectorStore` | Memory | pgvector (PostgreSQL) | セマンティックメモリの永続化・検索 |

---

## 各コンポーネント詳細

### 1. ChatUI
**レイヤー**: Frontend  
**技術**: Next.js 14+ / TypeScript  
**責務**:
- ユーザーのメッセージ入力とエージェント応答の表示
- FastAPI への HTTP/SSE リクエスト送信
- SSE ストリームの受信とリアルタイム文字表示
- Fitbit 認証状態（接続済み / 未接続）のインジケーター表示
- Fitbit OAuth2 認証フローの開始ボタン

**境界**: ブラウザとFastAPIバックエンドの間。ビジネスロジックは持たない。

---

### 2. FastAPIApp
**レイヤー**: Backend API  
**技術**: FastAPI (Python)  
**責務**:
- HTTP エンドポイントの定義とルーティング
- リクエストのバリデーション（Pydantic）
- Next.js からの CORS リクエストの許可
- AgentService への処理委譲
- Fitbit OAuth2 コールバックの受け取り

**エンドポイント**:
- `POST /chat` — チャットメッセージ受信・SSEストリーミング応答
- `GET /auth/fitbit` — OAuth2認証フロー開始（FitbitClientへ委譲）
- `GET /auth/fitbit/callback` — OAuth2コールバック処理
- `GET /health` — ヘルスチェック

**境界**: HTTPレイヤーのみ。ビジネスロジックは LangGraphAgent と FitbitClient に委譲。

---

### 3. LangGraphAgent
**レイヤー**: AI Agent  
**技術**: LangGraph (Python) — カスタムグラフ  
**責務**:
- カスタム ReAct ループのグラフ定義（ノード・エッジを手動実装）
- LLM（Claude）へのメッセージ送信・応答受信
- ToolRegistry のツール選択と呼び出し
- MemorySaver（ショートタームメモリ）によるセッション内の会話保持
- MemoryManager（ロングタームメモリ）からのコンテキスト注入・保存

**グラフ構造**:
```
[START]
  └─→ [memory_inject_node]   ← Long-term memory から関連情報を取得してコンテキストに注入
        └─→ [agent_node]     ← LLM 呼び出し（ツール使用判断）
              ├─→ [tool_node] ← ツール実行（条件: tool_calls あり）
              │     └─→ [agent_node]  （ループ）
              └─→ [memory_save_node]  ← 重要情報を Long-term memory に保存（条件: END前）
                    └─→ [END]
```

---

### 5. FitbitClient
**レイヤー**: Integration  
**技術**: Python クラス (`httpx` / `requests`)  
**責務**:
- Fitbit OAuth2 Authorization Code Flow の実装
- アクセストークン・リフレッシュトークンの管理（`.env` / ファイル）
- トークン期限切れ時の自動リフレッシュ
- Fitbit API エンドポイントへの認証付きリクエスト送信
- レスポンスの Python dict への変換

**管理するトークン状態**:
- `access_token`: Fitbit API 呼び出し用
- `refresh_token`: トークン更新用
- `expires_at`: 有効期限チェック用

---

### 6. ToolRegistry
**レイヤー**: AI Agent / Integration  
**技術**: LangChain `@tool` デコレータ  
**責務**:
- LangGraph エージェントに登録する全ツールの定義
- FitbitClient を通じた Fitbit データ取得ツール群
- プランニングロジックツール群

**定義するツール**（詳細は component-methods.md 参照）:
- Fitbit データ取得: `get_steps`, `get_calories_burned`, `get_weight`, `get_heart_rate`, `get_calories_in`
- プランニング: `calculate_calorie_deficit`, `generate_home_workout_plan`, `get_weekly_progress`

---

### 7. MemoryManager
**レイヤー**: Memory  
**技術**: Python クラス + LangChain `VectorStore`  
**責務**:
- Short-term memory（MemorySaver）と Long-term memory（VectorStore）の統合管理
- Long-term memory への情報保存（エンベディング生成 → pgvector へ保存）
- Long-term memory からの関連情報検索（セマンティック検索）
- 重要情報の更新・上書き（目標体重変更など）

---

### 8. VectorStore（PostgreSQL + pgvector）
**レイヤー**: Infrastructure / Memory  
**技術**: PostgreSQL + pgvector 拡張  
**責務**:
- セマンティックメモリの永続化（ベクトル + メタデータ）
- 類似度検索（コサイン類似度 / ユークリッド距離）
- ローカル実行: Docker Compose で PostgreSQL + pgvector を起動

**保存するデータ例**:
- ユーザーの目標体重・目標期間
- 食事の好み・制限
- 運動の好み・難易度設定
- 過去のプランサマリー
