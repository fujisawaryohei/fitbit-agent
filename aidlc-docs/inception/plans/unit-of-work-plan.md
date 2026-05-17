# Unit of Work Plan — Fitbit Weight Management AI Agent

## 実行ステップ

### PART 1: PLANNING
- [x] Step 1: ユニット分割方針の確定（3ユニット）
- [x] Step 2: 各ユニットの境界・責務の定義

### PART 2: GENERATION
- [x] Step 3: unit-of-work.md の生成
- [x] Step 4: unit-of-work-dependency.md の生成
- [x] Step 5: unit-of-work-story-map.md の生成

---

## 質問セクション

---

## Question 1
システムを何ユニットに分割しますか？

A) 2ユニット — Frontend（Next.js）/ Backend+Agent（FastAPI + LangGraph + Fitbit + Memory）
B) 3ユニット — Frontend / Backend API（FastAPI + Fitbit OAuth2）/ AI Agent Core（LangGraph + Tools + Memory）
C) 4ユニット — Frontend / Backend API / AI Agent Core / Fitbit Integration（FitbitClient + Tools）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2
ユニットの実装順序はどうしますか？

A) Backend/Agent を先に実装し、Frontend は後から繋ぐ
B) Frontend と Backend/Agent を並行して実装する
C) AI Agent Core → Backend API → Frontend の順で実装する
X) Other (please describe after [Answer]: tag below)

[Answer]: C: 最初はprintとかで上手く動作しているか確認しながら進めたい。また、languseとかでトレースを確認しながらデバックできたら嬉しい。dockerイメージのlangfuse使って、セルフホストのやつ使いたい。
