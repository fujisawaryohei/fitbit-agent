# Knowledge: project-frontend (fitbit-agent)

- **フレームワーク**: Next.js 16 (App Router) + TypeScript + Tailwind CSS、`frontend/` 配下
- **重要**: `frontend/AGENTS.md` に「This is NOT the Next.js you know」とある。
  **API を使う前に必ず `frontend/node_modules/next/dist/docs/` を読む。**

## ディレクトリ
```
frontend/src/
├── app/
│   ├── layout.tsx           # ヘッダー + サイドバー + main
│   ├── page.tsx             # トップ（Chat コンポーネント）
│   ├── chat/[chat_id]/      # 動的ルート
│   └── api/chat/route.ts    # Route Handler（SSE プロキシ）
├── components/              # Chat, ChatHistory, NewChatModal, MessageList, MessageInput, FitbitStatus
├── lib/api.ts              # fetchChats, fetchMessages, streamChat
└── types/chat.ts           # Message, Chat, ChatMessage, SSEChunk
```

## 主要パターン

### 動的ルートの params（Next.js 16）
```tsx
"use client"
import { useParams } from "next/navigation"
const params = useParams<{ chat_id: string }>()
```

### API クライアント
```ts
// /api/* は next.config.ts の rewrite で localhost:8000 にプロキシ
export const BACKEND_URL = "/api"
fetch(`${BACKEND_URL}/chats`, { credentials: "include" })
```

### SSEChunk 型
```ts
type SSEChunk = {
  type: "chunk" | "done" | "error"
  content: string
  session_id: string
  chat_id?: number  // done イベント時に設定
}
```

### Tailwind カラー
- ブランドカラー `#00B0B9`（Fitbit テーマ色）: `bg-[#00B0B9]` / `text-[#00B0B9]` / `focus:border-[#00B0B9]`

## 検証コマンド
- 型チェック: `cd frontend && npx tsc --noEmit`
