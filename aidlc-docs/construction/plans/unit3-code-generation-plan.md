# Code Generation Plan — Unit 3: Frontend

> **ペアプロ方針**: ナビゲーター(Claude) / ドライバー(ユーザー) 形式で進める。

## 技術スタック

| 技術 | 選定内容 |
|---|---|
| フレームワーク | Next.js 15 (App Router) |
| 言語 | TypeScript |
| スタイリング | Tailwind CSS |
| SSE クライアント | `fetch` + `ReadableStream`（EventSource は POST 非対応のため）|
| バックエンド URL | `http://localhost:8000` |

---

## ディレクトリ構成

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # ルートレイアウト
│   │   ├── page.tsx             # メインチャットページ
│   │   └── globals.css
│   ├── components/
│   │   ├── Chat.tsx             # チャット UI 全体
│   │   ├── MessageList.tsx      # メッセージ一覧
│   │   ├── MessageInput.tsx     # 入力フォーム
│   │   └── FitbitStatus.tsx     # 接続ステータス + 認証ボタン
│   ├── lib/
│   │   └── api.ts               # SSE クライアント・API ユーティリティ
│   └── types/
│       └── chat.ts              # SSEChunk・Message 型定義
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.ts
```

---

## Milestone 1: プロジェクトセットアップ

### Step 1: Next.js プロジェクト作成

- [x] `frontend/` ディレクトリに Next.js プロジェクトを作成
  ```bash
  npx create-next-app@latest frontend \
    --typescript --tailwind --eslint \
    --app --src-dir --import-alias "@/*" --no-git
  ```
- [x] デフォルトコンテンツ（`page.tsx` の中身）を削除

### Step 2: 型定義

- [x] `src/types/chat.ts` を作成
  - `SSEChunk`: `type`, `content`, `session_id`
  - `Message`: `role ("user" | "assistant")`, `content`, `id`

### Step 3: API クライアント

- [x] `src/lib/api.ts` を作成
  - `BACKEND_URL = "http://localhost:8000"` 定数
  - `streamChat()`: ペアプロで実装予定（stub のみ）

---

## Milestone 2: UI コンポーネント実装

### Step 4: FitbitStatus コンポーネント

- [x] `src/components/FitbitStatus.tsx` を作成
  - Cookie `fitbit_user_id` の有無で接続状態を判定
  - 接続済み: 緑バッジ「Fitbit 接続済み」
  - 未接続: 「Fitbit と連携する」ボタン → `http://localhost:8000/auth/fitbit` にリダイレクト

### Step 5: MessageList コンポーネント

- [x] `src/components/MessageList.tsx` を作成
  - `Message[]` を受け取り user / assistant を色分けして表示
  - ストリーミング中のメッセージにカーソルアニメーション

### Step 6: MessageInput コンポーネント

- [x] `src/components/MessageInput.tsx` を作成
  - テキストエリア + 送信ボタン
  - ストリーミング中は無効化
  - `Shift+Enter` で改行、`Enter` で送信

### Step 7: Chat コンポーネント

- [x] `src/components/Chat.tsx` を作成
  - `MessageList` + `MessageInput` を統合
  - `session_id` は `crypto.randomUUID()` で生成してローカル保持
  - `streamChat()` 呼び出し部分はペアプロで実装予定（TODO）

### Step 8: メインページ

- [x] `src/app/page.tsx` を作成
  - `FitbitStatus` + `Chat` を配置

---

## Milestone 3: 動作確認

- [ ] `npm run dev` でサーバー起動（`localhost:3000`）
- [ ] バックエンド（`localhost:8000`）を起動した状態で動作確認
  - [ ] 未認証状態で「Fitbit と連携する」ボタンが表示される
  - [ ] 認証済み状態で「Fitbit 接続済み」バッジが表示される
  - [ ] チャット送信でストリーミング応答が表示される
  - [ ] 認証なしでチャット送信すると 401 エラーが適切に表示される
