# Policy: immutability

**既存オブジェクトを破壊的に変更せず、常に新しいオブジェクトを作る。**

```
WRONG:  modify(original, field, value) → original をその場で書き換える
CORRECT: update(original, field, value) → 変更を加えた新コピーを返す
```

理由: イミュータブルなデータは隠れた副作用を防ぎ、デバッグを容易にし、安全な並行処理を可能にする。
