# ngrok でフロントエンドとバックエンドに同じ URL が割り当てられる

## 現象

`ngrok start --all` で2トンネルを同時起動すると、フロントエンド（3000）とバックエンド（8000）に同じ FQDN が割り当てられる。

```
Forwarding  https://xxxx.ngrok-free.dev -> http://localhost:3000
Forwarding  https://xxxx.ngrok-free.dev -> http://localhost:8000  # 同じ URL！
```

## 原因

ngrok 無料プランは1アカウントにつき URL が1つのみ。2トンネルを起動しても同じ URL になる。

## 解決

Next.js をリバースプロキシとして使い、**ngrok は port 3000 の1本のみ**公開する。

```
iPad
 └─ ngrok(3000) → Next.js
                    ├─ /api/chat  → Route Handler → FastAPI(8000)  ← SSE対応
                    ├─ /api/*     → rewrite        → FastAPI(8000)
                    └─ /auth/*    → rewrite        → FastAPI(8000)
```

```typescript
// next.config.ts
async rewrites() {
  return [
    { source: "/api/:path*",  destination: "http://localhost:8000/:path*" },
    { source: "/auth/:path*", destination: "http://localhost:8000/auth/:path*" },
  ];
}
```

## 対象ファイル

- `frontend/next.config.ts`
- `Makefile`（`ngrok http 3000` のみに変更）
