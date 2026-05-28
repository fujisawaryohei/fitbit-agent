# iPad でスタイルが全く適用されない

## 現象

iPad ブラウザから ngrok URL にアクセスすると、Tailwind のスタイルが一切適用されず素の HTML が表示される。

## 原因（複数重なっていた）

### 1. `globals.css` のデフォルトスタイルが Tailwind を上書き

`create-next-app` で生成された `globals.css` にダークモード対応の `body` スタイルがあり、
Tailwind のクラスより優先されていた。

```css
/* これが Tailwind クラスを上書きしていた */
body {
  background: var(--background);  /* ダークモード時は #0a0a0a */
  color: var(--foreground);
}
```

### 2. `basePath` の誤設定

プロキシ経由アクセスを誤って `basePath` で解決しようとしたが、プロキシはプレフィックスを剥がして転送するため 404 になった。

## 解決

`globals.css` を `@import "tailwindcss"` だけにシンプル化。

```css
/* after */
@import "tailwindcss";
```

`basePath` は削除。プロキシはプレフィックスを剥がして `localhost:3000/` に転送するため不要。

## 対象ファイル

- `frontend/src/app/globals.css`
- `frontend/next.config.ts`
