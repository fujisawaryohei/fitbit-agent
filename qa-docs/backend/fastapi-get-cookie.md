# FastAPI / Next.js Route Handler で Cookie の値を取り出す方法

## FastAPI

```python
from fastapi import Cookie, Request

# 方法1: Cookie パラメータ（推奨）
@router.get("/example")
def example(fitbit_user_id: str | None = Cookie(default=None)):
    print(fitbit_user_id)

# 方法2: Request オブジェクトから直接
@router.get("/example")
def example(request: Request):
    fitbit_user_id = request.cookies.get("fitbit_user_id")
```

方法1はバリデーション・型安全・デフォルト値設定が容易なため推奨。
方法2は複数 Cookie を動的に取得したい場合に使う。

## Next.js Route Handler

```typescript
import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  // 方法1: cookies() メソッド（値だけ取得）
  const fitbitUserId = request.cookies.get("fitbit_user_id")?.value;

  // 方法2: Cookie ヘッダーをそのまま文字列で取得（バックエンドへ転送する場合）
  const cookieHeader = request.headers.get("cookie") ?? "";
}
```

バックエンドにリクエストを転送する際は方法2でヘッダーをそのまま渡す。

## プロジェクト内での使用箇所

- `backend/controllers/chat.py` → FastAPI 方法1（`Cookie(default=None)`）
- `frontend/src/app/api/chat/route.ts` → Next.js 方法2（ヘッダーをバックエンドへ転送）
