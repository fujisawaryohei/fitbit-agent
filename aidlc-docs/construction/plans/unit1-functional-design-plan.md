# Functional Design Plan — Unit 1: AI Agent Core

## 実行ステップ

- [x] Step 1: ビジネスロジックモデルの設計（質問回答後）
- [x] Step 2: ドメインエンティティの定義
- [x] Step 3: ビジネスルールの定義
- [x] Step 4: PBT-01 テスト可能プロパティの特定

## 対象ストーリー
US-02, US-04〜07, US-09〜15（AI Agent Core の全ストーリー）

---

## 質問セクション

---

## Question 1
カロリー赤字計算（US-10）のロジックはどうしますか？

A) 固定算式 — 体重1kg = 7,200kcal の法則を使い、目標達成に必要な1日の赤字カロリーを計算する
B) ユーザー指定ペース — 「週に何kg落とすか」をユーザーが指定し、そこから必要カロリーを逆算する
C) 両方対応 — デフォルトは週0.5kgペースを提案しつつ、ユーザーが変更できる
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 2
自宅運動プラン（US-12）の生成ロジックはどうしますか？

A) LLM完全委任 — エージェントのプロンプトに「自宅運動プランを生成して」と指示し、LLMが種目・回数・フォームを生成する
B) ルールベース + LLM — 種目・消費カロリーのテーブルをコードで持ち、LLMはフォーム説明と週次スケジュールの文章生成のみ担当する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
Long-term memory（US-15）への保存タイミングと抽出方法はどうしますか？

A) 毎ターン保存 — 会話終了時に LLM が「重要情報を要約して」と指示し、返ってきたテキストをベクトル化して保存する
B) キーワードトリガー — 目標体重・食事・運動の好みに関連するキーワードが含まれる場合のみ保存する
C) 構造化抽出 — LLM に JSON 形式（`{"goal_weight": ..., "preference": ...}`）で抽出させてから保存する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
`AgentState`（LangGraph の状態）に `messages` と `session_id` 以外に持たせたい情報はありますか？

A) なし — messages と session_id のみでシンプルに始める
B) あり — `user_goal`（目標体重・期間）を状態として持ち、全ノードからアクセスできるようにする
C) あり — `fitbit_cache`（当日取得済みデータのキャッシュ）も持ち、同一セッション内で重複APIコールを防ぐ
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
FitbitClient のデータ取得メソッドで、日付のデフォルト値はどうしますか？

A) 常に "today" をデフォルトにする（エージェントが明示的に日付を渡さなければ今日のデータを返す）
B) デフォルトなし — 必ずエージェント（LLM）が日付を明示的に指定する
C) 「today」と「過去7日分」を使い分けられるようにする（`date` と `period` 引数を持つ）
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 6
Fitbit API のエラー（レート制限・トークン切れ・データなし）はどう扱いますか？

A) シンプル — エラー時はエラーメッセージを文字列でツールの戻り値として返し、LLM がユーザーに自然言語で伝える
B) 例外スロー — Python の例外を raise し、FastAPI 側でキャッチして HTTP エラーを返す
C) リトライあり — 一時的なエラー（429/503）はリトライし、それでも失敗したら A と同様にエラーメッセージを返す
X) Other (please describe after [Answer]: tag below)

[Answer]: A
