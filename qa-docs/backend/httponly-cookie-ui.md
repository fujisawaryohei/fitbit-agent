# HttpOnly Cookie を JS から読めず Fitbit 接続状態が表示されない

## 現象

Fitbit 認証完了後も「Fitbit と連携する」ボタンが消えず、接続済みバッジが表示されない。

## 原因

`fitbit_user_id` Cookie を `httponly=True` でセットしていたため、`document.cookie` で読めず、
フロントエンドが接続状態を判定できなかった。

```python
# httponly=True → JS から読めない
response.set_cookie(key="fitbit_user_id", value=..., httponly=True)
```

## 解決

UI 表示専用の補助 Cookie `fitbit_connected=true`（非 HttpOnly）を追加する二重 Cookie パターンを採用。

| Cookie | HttpOnly | 用途 |
|---|---|---|
| `fitbit_user_id` | `True` | バックエンド認証（JS からは読めない） |
| `fitbit_connected` | `False` | UI 表示切り替え専用（値は `true` のみ） |

```python
redirect.set_cookie(key="fitbit_user_id", value=user.fitbit_user_id, httponly=True, samesite="lax")
redirect.set_cookie(key="fitbit_connected", value="true", httponly=False, samesite="lax")
```

フロントエンドは `fitbit_connected` Cookie の有無だけを確認する。

```typescript
function isFitbitConnected(): boolean {
  return /(?:^|;\s*)fitbit_connected=true/.test(document.cookie);
}
```

## 対象ファイル

- `backend/controllers/auth.py`
- `frontend/src/components/FitbitStatus.tsx`
