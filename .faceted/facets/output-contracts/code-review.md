# Output Contract: code-review

レビュー結果は重大度ごとに分類して出力する。

```
## サマリ
<全体評価を 1〜2 文>

## 指摘
### 🔴 CRITICAL
- `file:line` — <問題> / <修正案>
### 🟠 HIGH
- ...
### 🟡 MEDIUM
- ...
### 🟢 LOW / Nit
- ...

## 良い点
- <評価できる点>
```

- CRITICAL・HIGH は必ず是正対象、MEDIUM は可能な限り対応。
- 各指摘は `file:line` と具体的な修正案を伴う。
