# NFR Requirements Plan — Unit 1: AI Agent Core

## 実行ステップ

- [x] Step 1: NFR 質問への回答収集
- [x] Step 2: nfr-requirements.md の生成
- [x] Step 3: tech-stack-decisions.md の生成

## 対象ストーリー
US-02, US-04〜07, US-09〜15（AI Agent Core の全ストーリー）

---

## 質問セクション

---

## Question 1
Long-term memory（US-15）で pgvector に保存するベクトルの**埋め込みモデル**はどれを使いますか？

A) OpenAI text-embedding-3-small — API 経由（有料）、1536次元、日本語対応、品質高い
B) intfloat/multilingual-e5-small — ローカル実行（無料）、384次元、日本語対応、軽量
C) intfloat/multilingual-e5-large — ローカル実行（無料）、1024次元、日本語対応、高品質
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 2
Short-term memory（US-14）の MemorySaver はどこに保存しますか？

A) インメモリのみ — プロセス再起動でセッションリセット（Unit 1 の開発・動作確認に十分）
B) SQLite 永続化 — LangGraph の SqliteSaver を使用、プロセス再起動後もセッションを維持
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
エージェントのレスポンス方式はどうしますか？（Unit 1 時点での実装方針）

A) ストリーミング — `agent.stream()` を使い、LLM がトークンを生成するたびにリアルタイム出力する
B) バッチ — `agent.invoke()` を使い、全回答が揃ってから一括返却する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---
