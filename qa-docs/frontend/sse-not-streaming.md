# チャット送信後に SSE レスポンスが画面に表示されない

## 現象

チャットメッセージを送信すると 200 は返るが、ストリーミングテキストが画面に届かない。
サーバーログでは `AIMessageChunk` が正常に届いていることを確認済み。

## 原因

Next.js の `rewrites` は SSE（Server-Sent Events）レスポンスをバッファリングしてしまい、
チャンクが溜まってから一括送信になるためリアルタイム表示にならない。

```
ブラウザ → /api/chat → Next.js rewrite → FastAPI
                          ↑ ここでバッファリング発生
```

## 解決

`/api/chat` だけ Next.js Route Handler を作成し、`ReadableStream` をそのまま返すことでバッファリングを回避。

```typescript
// frontend/src/app/api/chat/route.ts
export async function POST(request: NextRequest) {
  const backendResponse = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: request.headers.get("cookie") ?? "",
    },
    body: JSON.stringify(await request.json()),
  });

  // ReadableStream をそのまま返すことで SSE をバッファリングせずに流す
  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
```

Route Handler はファイルパスが同名の rewrite より優先されるため、
`next.config.ts` の rewrite 設定はそのままでよい。

## 対象ファイル

- `frontend/src/app/api/chat/route.ts`（新規作成）
