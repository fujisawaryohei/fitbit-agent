# NFR Design Plan — Unit 1: AI Agent Core

## 実行ステップ

- [x] Step 1: NFR Design 質問への回答収集
- [x] Step 2: nfr-design-patterns.md の生成
- [x] Step 3: logical-components.md の生成

---

## 質問セクション

---

## Question 1
`SentenceTransformer("intfloat/multilingual-e5-large")` の初期化タイミングはどうしますか？
（初回ロードは 560MB のモデルダウンロード + 数秒の初期化が発生します）

A) 起動時ロード — アプリ起動時にモデルを一度だけ初期化してシングルトンとして保持する（最初の会話は速い）
B) 遅延ロード — 初回の `memory_save_node` 実行時に初期化する（起動は速いが初回会話で遅延が発生）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
pgvector（PostgreSQL）への接続方式はどうしますか？

A) 都度接続 — `MemoryManager` のメソッド呼び出しごとに接続・切断する（シンプル、PoC 向き）
B) コネクションプール — `psycopg2.pool.SimpleConnectionPool` を使い、接続を再利用する（少し複雑だが実践的）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---
