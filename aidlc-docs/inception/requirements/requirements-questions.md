# Requirements Clarification Questions — Fitbit Agent

Fitbitエージェントの設計に必要な情報を収集します。
各質問の `[Answer]:` タグの後に選択肢の英字（A, B, C...）を入力してください。
選択肢に該当するものがない場合は「X」を選び、内容を `[Answer]:` の後に記述してください。

---

## Question 1
Fitbitエージェントの主な目的は何ですか？

A) 健康データ（歩数・心拍数・睡眠など）を定期的に収集・記録する
B) 収集データを分析・可視化してインサイトを提供する
C) データ収集 + 分析 + 通知（特定条件でアラート）を行う
D) 他のサービス（Slack, LINE, メール等）へのデータ転送・通知が主目的
X) Other (please describe after [Answer]: tag below)

[Answer]: X: Fitbitから健康データ(歩数、心拍数、体重、摂取カロリー)などのデータを取得して、目標体重に落とすためのプランニングをしてくれるAIエージェントの構築(摂取カロリーや運動の内容。運動の内容はジムなどを利用せず、自宅でもできるものとする。)

---

## Question 2
エージェントが取得・活用するFitbitデータの種類を選んでください（主なもの）。

A) 活動量のみ（歩数・消費カロリー・移動距離）
B) 心拍数・SpO2（血中酸素）を含む身体指標
C) 睡眠データ（睡眠時間・睡眠ステージ）を含む
D) 上記すべて（活動量 + 心拍 + 睡眠 + その他）
X) Other (please describe after [Answer]: tag below)

[Answer]: X: Question1の目的に沿ったデータ全て

---

## Question 3
エージェントの動作トリガーはどれですか？

A) 定期実行（スケジュール。例：毎日朝8時に取得）
B) ユーザーからの明示的なリクエスト（チャットやAPIへの問い合わせ）
C) 定期実行 + オンデマンド（両方対応）
D) Fitbitデータの変化を検知してリアルタイムに反応する
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4
エージェントの出力先・通知先はどこですか？

A) Slack（チャンネルへの投稿）
B) データベース or ファイルへの保存のみ（後から参照）
C) LINEやメール等の通知サービス
D) 複数の出力先（DB保存 + 通知）
X) Other (please describe after [Answer]: tag below)

[Answer]: X: チャットアプリを想定。フロントエンド側で表示する。

---

## Question 5
AIによる「エージェント的」な振る舞いとして期待することはどれに近いですか？

A) データを取得・整形して渡すだけ（ツール的な動作、AIの自律判断は不要）
B) データを取得後、LLMが自然言語でサマリーや考察を生成する
C) LLMが複数ツールを自律的に呼び出してタスクを完遂する（ReActエージェントなど）
D) ユーザーと対話しながらFitbitデータについて質問に答えるチャットボット
X) Other (please describe after [Answer]: tag below)

[Answer]: B, C

---

## Question 6
使用するプログラミング言語・フレームワークの希望はありますか？

A) Python（LangChain / LangGraph）
B) Python（Anthropic SDK 直接利用）
C) Python（フレームワーク未定・柔軟に）
D) その他の言語（TypeScript等）
X) Other (please describe after [Answer]: tag below)

[Answer]: A, X: FastAPI, NextJS, TypeScript

---

## Question 7
実行・デプロイ環境の希望はありますか？

A) ローカル実行のみ（開発・個人利用）
B) AWS Lambda（サーバーレス）
C) AWS EC2 / ECS（常時起動型）
D) デプロイ先は設計後に検討する
X) Other (please describe after [Answer]: tag below)

[Answer]: X: 完成後ローカル実行を完了させた後に一緒に考えたい

---

## Question 8
Fitbit API認証について、現状はどれに近いですか？

A) Fitbit OAuth2トークンはすでに取得済み（または取得方法は知っている）
B) OAuth2フローの実装も含めて設計してほしい
C) 個人用トークン（Personal Access Token）を使う想定
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question: Security Extension
このプロジェクトにセキュリティ拡張ルールを適用しますか？

A) Yes — すべてのSECURITYルールをブロッキング制約として適用（本番グレードのアプリに推奨）
B) No — SECURITYルールをスキップ（PoC・プロトタイプ・実験的プロジェクトに適切）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question: Property-Based Testing Extension
プロパティベーステスト（PBT）ルールを適用しますか？

A) Yes — すべてのPBTルールをブロッキング制約として適用（ビジネスロジックやデータ変換が複雑なプロジェクトに推奨）
B) Partial — 純粋関数とシリアライズの往復テストにのみPBTを適用
C) No — PBTルールをスキップ（シンプルなCRUDやUI専用プロジェクトに適切）
X) Other (please describe after [Answer]: tag below)

[Answer]: A
