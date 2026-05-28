# 送信ボタンが押下後に無効のまま戻らない

## 現象

チャットメッセージを送信後、送信ボタンが無効（disabled）のままになり操作できなくなる。

## 原因

`handleSend` 内で `streamChat()` が例外をスローした場合、`onDone` も `onError` も呼ばれないため
`setStreaming(false)` が実行されずボタンが永久に無効になる。

```typescript
// before: 例外時に streaming が解除されない
setStreaming(true);
await streamChat(text, sessionId, onChunk, onDone, onError);
// ↑ 例外が発生すると onDone/onError が呼ばれない → setStreaming(false) が実行されない
```

## 解決

`streamChat` の呼び出しを `try/catch` で囲み、例外発生時も必ず `setStreaming(false)` を呼ぶ。

```typescript
setStreaming(true);
try {
  await streamChat(text, sessionId, onChunk, onDone, onError);
} catch (e) {
  setMessages((prev) => {
    const updated = [...prev];
    updated[updated.length - 1] = {
      ...updated[updated.length - 1],
      content: `エラー: ${e instanceof Error ? e.message : String(e)}`,
    };
    return updated;
  });
  setStreaming(false);
}
```

## 対象ファイル

- `frontend/src/components/Chat.tsx`
