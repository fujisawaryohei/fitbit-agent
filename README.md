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

`.env.example` をコピーして `.env` を作成してください。

```bash
cp .env.example .env
```

| 変数名 | 説明 | デフォルト |
|---|---|---|
| `FITBIT_CLIENT_ID` | Fitbit アプリのクライアント ID | — |
| `FITBIT_CLIENT_SECRET` | Fitbit アプリのクライアントシークレット | — |
| `FITBIT_REDIRECT_URI` | Fitbit OAuth2 コールバック URL | `http://localhost:8000/auth/fitbit/callback` |
| `FRONTEND_URL` | 認証完了後のリダイレクト先（FastAPI → フロントへのリダイレクト） | `http://localhost:3000` |
| `CORS_ORIGINS` | 追加許可オリジン（カンマ区切り）。ngrok 使用時に設定 | — |
| `PGVECTOR_DSN` | PostgreSQL 接続文字列 | — |
| `LANGCHAIN_TRACING_V2` | LangSmith トレース有効化（任意） | `false` |

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

> Next.js が `/api/*`・`/auth/*` を FastAPI にプロキシするため、ngrok は1つで済みます。  
> チャットの SSE ストリーミングは Route Handler 経由で転送されます。

```
iPad
 │
 ▼
ngrok → Next.js (port 3000)
              │
              ├─ /api/chat  → Route Handler → FastAPI (SSE ストリーミング)
              ├─ /api/*     → rewrite       → FastAPI (port 8000)
              └─ /auth/*    → rewrite       → FastAPI (port 8000)
```

ターミナルを3つ開いて実行します。

**① まず ngrok を起動して URL を確認します**

```bash
# ターミナル 3: ngrok トンネル
make ngrok
# → Forwarding https://xxxx.ngrok-free.dev -> http://localhost:3000 の URL をメモ
```

**② `.env` を ngrok の URL に更新します**

```env
FITBIT_REDIRECT_URI=https://xxxx.ngrok-free.dev/auth/fitbit/callback
FRONTEND_URL=https://xxxx.ngrok-free.dev
CORS_ORIGINS=https://xxxx.ngrok-free.dev
```

> Fitbit Developer ダッシュボードの **Callback URL** にも同じ URL を登録してください。

**③ バックエンド・フロントエンドを起動します**

```bash
# ターミナル 1: バックエンド
make server

# ターミナル 2: フロントエンド
make frontend
```

iPad から `https://xxxx.ngrok-free.dev` にアクセスします。

---

## Makefile コマンド一覧

| コマンド | 内容 |
|---|---|
| `make server` | FastAPI バックエンドを起動（port 8000、`FRONTEND_URL` を参照） |
| `make frontend` | Next.js フロントエンドを起動（port 3000） |
| `make ngrok` | ngrok でポート 3000 を公開（iPad 開発用） |

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
uv run pytest agent/tests/ backend/tests/ --ignore=agent/tests/test_planning_tools_llm.py -q

# カバレッジ付き
uv run pytest --cov=backend --cov=agent --cov-report=term-missing \
  --ignore=agent/tests/test_planning_tools_llm.py -q
```
