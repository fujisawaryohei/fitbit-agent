# Chrome が注入した属性で React hydration エラーが発生する

## 現象

ブラウザコンソールに以下の hydration ミスマッチエラーが表示される。

```
A tree hydrated but some attributes of the server rendered HTML didn't match the client properties.
  - __gchrome_remoteframetoken="..."   ← html タグに注入
  - __gchrome_uniqueid="1"             ← textarea タグに注入
```

## 原因

Chrome のリモートデバッグ機能が `<html>` や `<textarea>` に独自属性を注入する。
SSR 時には存在しない属性がクライアント側で追加されるため、React の hydration が失敗する。

コードのバグではなく Chrome の動作による。

## 解決

注入対象の要素に `suppressHydrationWarning` を追加して React の警告を抑制する。

```tsx
// layout.tsx
<html lang="ja" suppressHydrationWarning>

// MessageInput.tsx
<textarea suppressHydrationWarning ... />
```

## 対象ファイル

- `frontend/src/app/layout.tsx`
- `frontend/src/components/MessageInput.tsx`
