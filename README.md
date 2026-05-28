# Fitbit AI アシスタント

Fitbit の健康データをもとに、AI がダイエット・フィットネスをサポートするチャットアプリケーションです。

## 概要

- **チャット UI** から日本語で質問すると、AI が Fitbit データを取得・分析して回答します
- **歩数・消費カロリー・体重・心拍数・摂取カロリー** などのデータを参照できます
- **カロリー赤字計算・運動プラン生成・週次進捗評価** などのプランニング機能も備えています
- Fitbit OAuth2 認証により、アクセストークンは DB に安全に保存されます

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | Next.js 15 / TypeScript / Tailwind CSS |
| バックエンド | FastAPI / Python 3.13 |
| AI エージェント | LangGraph / Amazon Bedrock (Claude Haiku) |
| 埋め込みモデル | Amazon Titan Embed Text v2 (Bedrock) |
| データベース | PostgreSQL + pgvector |
| 認証 | Fitbit OAuth2 / Cookie (HttpOnly) |

---

## セットアップ

### 前提条件

- Python 3.11+、`uv` コマンド
- Node.js 20+、`npm`
- Docker（PostgreSQL + pgvector 用）
- AWS 認証情報（EC2 インスタンスプロファイル、または `~/.aws/credentials`）
- Fitbit Developer アカウント（[dev.fitbit.com](https://dev.fitbit.com)）

### 環境変数

`.env` ファイルをプロジェクトルートに作成してください。

```env
# Fitbit OAuth2
FITBIT_CLIENT_ID=your_client_id
FITBIT_CLIENT_SECRET=your_client_secret
FITBIT_REDIRECT_URI=http://localhost:8000/auth/fitbit/callback

# PostgreSQL
PGVECTOR_DSN=postgresql://user:password@localhost:5432/fitbit_memory

# LangSmith（任意）
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=fitbit-agent
```

### DB 起動

```bash
docker compose up -d
uv run alembic upgrade head
```

### 依存パッケージのインストール

```bash
# Python
uv sync

# Node.js
cd frontend && npm install
```

---

## 起動方法

### 通常の PC（ローカル開発）

ターミナルを2つ開いて実行します。

```bash
# ターミナル 1: バックエンド
make server

# ターミナル 2: フロントエンド
make frontend
```

ブラウザで `http://localhost:3000` にアクセスします。

### iPad / スマートフォンからアクセス（ngrok 使用）

> Next.js が `/api/*` を FastAPI にリバースプロキシするため、ngrok は1つで済みます。

```
iPad
 │
 ▼
ngrok → Next.js (port 3000)
              │
              └─ /api/* → FastAPI (port 8000)
                               │
                               ├─ LangGraph Agent (Bedrock)
                               ├─ Fitbit API
                               └─ PostgreSQL + pgvector
```

ターミナルを3つ開いて実行します。

```bash
# ターミナル 1: バックエンド
make server

# ターミナル 2: フロントエンド
make frontend

# ターミナル 3: ngrok トンネル
make ngrok
```

ngrok 起動後に表示される URL（例: `https://xxxx.ngrok-free.dev`）にアクセスします。

---

## Makefile コマンド一覧

| コマンド | 内容 |
|---|---|
| `make server` | FastAPI バックエンドを起動（port 8000） |
| `make frontend` | Next.js フロントエンドを起動（port 3000） |
| `make ngrok` | ngrok でポート 3000 を公開 |

---

## 初回利用フロー

1. バックエンド・フロントエンドを起動
2. `http://localhost:3000`（または ngrok URL）にアクセス
3. 「Fitbit と連携する」ボタンをクリックして OAuth2 認証
4. 認証完了後、チャット画面から話しかける

---

## テスト

```bash
# 全テスト実行（LLM テストを除く）
uv run pytest agent/tests/ app/tests/ --ignore=agent/tests/test_planning_tools_llm.py -q

# カバレッジ付き
uv run pytest --cov=app --cov=agent --cov-report=term-missing \
  --ignore=agent/tests/test_planning_tools_llm.py -q
```
