# Application Design Plan — Fitbit Weight Management AI Agent

## 実行ステップ

- [x] Step 1: コンポーネント境界の確定（質問回答後）
- [x] Step 2: components.md の生成
- [x] Step 3: component-methods.md の生成
- [x] Step 4: services.md の生成
- [x] Step 5: component-dependency.md の生成
- [x] Step 6: application-design.md（統合ドキュメント）の生成

---

## 質問セクション

以下の質問に回答してください。各 `[Answer]:` の後に選択肢の英字を入力してください。

---

## Question 1
LangGraph エージェントと FastAPI バックエンドの配置はどちらを希望しますか？

A) 同一プロセス — FastAPI 内にエージェントを直接組み込む（シンプル・ローカル実行向き）
B) 別プロセス — FastAPI と LangGraph を別々のサービスとして起動する（将来のスケールアウトを考慮）
X) Other (please describe after [Answer]: tag below)

[Answer]: A: 将来的にBに移行できるよう設計は行なっておきたい

---

## Question 2
チャットのストリーミング応答はどの方式を希望しますか？

A) SSE（Server-Sent Events）— FastAPI から Next.js へ一方向ストリーミング（シンプルな実装）
B) WebSocket — 双方向通信（リアルタイム性が高いが実装が複雑）
C) ストリーミングなし — 応答が完成してから一括返却（シンプルだが UX がやや劣る）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
セマンティックメモリ（ロングタームメモリ）のベクトルストアはどれを使いますか？

A) Chroma — ローカルファイルに永続化・Python ネイティブ・セットアップが簡単
B) FAISS — インメモリ高速検索・Facebook製・ファイル保存も可能
C) LangGraph Store（InMemoryStore / 組み込み）— LangGraph 標準の memory store を使う
X) Other (please describe after [Answer]: tag below)

[Answer]: X: postgresql pgvector

---

## Question 4
LangGraph のグラフ構造はどちらを希望しますか？

A) `create_react_agent`（プリビルト）— LangGraph が提供するReActエージェントをそのまま使う（実装が速い）
B) カスタムグラフ — ノード・エッジを自分で定義し、メモリ管理や条件分岐を細かく制御する
X) Other (please describe after [Answer]: tag below)

[Answer]: B: 学習目的が強いので、ReActエージェントの実装は自分で行いたい

---

## Question 5
In-context memory（ショートタームメモリ）のセッション管理はどうしますか？

A) LangGraph Checkpointer（MemorySaver）— LangGraph 標準のインメモリチェックポインタ（セッション内で会話を保持）
B) LangGraph Checkpointer（SqliteSaver）— SQLite に永続化（プロセス再起動後も保持）
C) カスタム実装 — messages リストを FastAPI のセッションで管理する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
Fitbit API クライアントのアーキテクチャはどうしますか？

A) シンプルなモジュール — `fitbit_client.py` に関数を定義し、各 tool から直接呼び出す
B) クラスベース — `FitbitClient` クラスを作り、トークン管理・リフレッシュ・API呼び出しをカプセル化する
X) Other (please describe after [Answer]: tag below)

[Answer]: B
