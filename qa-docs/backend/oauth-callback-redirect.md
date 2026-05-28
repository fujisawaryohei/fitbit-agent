# OAuth2 コールバック後に 404 になる

## 現象

Fitbit 認証後のコールバックで Next.js 側に `/auth/fitbit/callback` リクエストが届き 404 になる。

## 原因

1. コールバックエンドポイントが JSON を返していたため、Fitbit 認証後の遷移先がなかった
2. `FITBIT_REDIRECT_URI` が ngrok URL でない場合、Fitbit から直接 FastAPI (port 8000) に戻るが、ngrok 経由では `/auth/*` が Next.js に届き FastAPI に転送されていなかった

## 解決

### 1. コールバックを `RedirectResponse` に変更

```python
# before
return AuthCallbackResponse(fitbit_user_id=user.fitbit_user_id, scope=user.scope)

# after
redirect = RedirectResponse(url=_FRONTEND_URL, status_code=302)
redirect.set_cookie(key="fitbit_user_id", value=user.fitbit_user_id, httponly=True, samesite="lax")
redirect.set_cookie(key="fitbit_connected", value="true", httponly=False, samesite="lax")
return redirect
```

`FRONTEND_URL` 環境変数でリダイレクト先を切り替え（ローカル: `http://localhost:3000` / ngrok: `https://xxxx.ngrok-free.dev`）。

### 2. Next.js のリライトに `/auth/*` を追加

```typescript
// next.config.ts
{
  source: "/auth/:path*",
  destination: "http://localhost:8000/auth/:path*",
}
```

### 3. ngrok 使用時の環境変数

```env
FITBIT_REDIRECT_URI=https://xxxx.ngrok-free.dev/auth/fitbit/callback
FRONTEND_URL=https://xxxx.ngrok-free.dev
```

## 対象ファイル

- `app/controllers/auth.py`
- `frontend/next.config.ts`
