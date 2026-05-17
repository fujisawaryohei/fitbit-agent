# Unit of Work Dependency — Fitbit Weight Management AI Agent

## 依存関係マトリクス

| ユニット | 依存先ユニット | 依存の種類 | 理由 |
|---------|--------------|-----------|------|
| Unit 1: AI Agent Core | なし | — | 独立して実装・テスト可能 |
| Unit 2: Backend API | Unit 1 | ランタイム依存 | FastAPI が LangGraphAgent を直接呼び出す |
| Unit 3: Frontend | Unit 2 | ランタイム依存 | Next.js が FastAPI エンドポイントに HTTP/SSE で接続 |

## 実装シーケンス

```
[Unit 1: AI Agent Core]
        |
        | 動作確認（print / LangFuse トレース）
        v
[Unit 2: Backend API]
        |
        | 動作確認（curl / Postman + LangFuse）
        v
[Unit 3: Frontend]
        |
        | 動作確認（ブラウザ E2E）
        v
[完成]
```

## インターフェース（ユニット間の接点）

### Unit 1 → Unit 2 の接点
- `LangGraphAgent.stream(message, session_id)` を FastAPI から呼び出し
- 戻り値: `AsyncIterator[str]`（SSE チャンク用）

### Unit 2 → Unit 3 の接点
- `POST /chat` — `Content-Type: text/event-stream`（SSE）
- `GET /auth/fitbit` — `302 Redirect`
- `GET /auth/fitbit/callback` — `200 JSON`
- `GET /health` — `200 JSON`

## 共有インフラ（全ユニット共通）

| リソース | 用途 | ユニット |
|---------|------|---------|
| PostgreSQL + pgvector | Long-term memory | Unit 1 |
| LangFuse + PostgreSQL | LLM トレース観測 | Unit 1, 2 |
| `.env` | APIキー・トークン管理 | Unit 1, 2 |
