# Business Rules — Unit 1: AI Agent Core

## BR-01: 減量ペースの安全制約

| ルール | 内容 |
|---|---|
| BR-01-1 | `pace_kg_per_week` の最大値は **1.0 kg**（急激な減量は健康リスクがあるため） |
| BR-01-2 | `daily_deficit_kcal` は **200〜1000 kcal** の範囲内でなければならない |
| BR-01-3 | 目標体重 `target_weight_kg` は現在体重 `current_weight_kg` より軽くなければならない |
| BR-01-4 | デフォルトペースは **0.5 kg/週**（安全かつ持続可能なペース） |

---

## BR-02: Fitbit API データ取得

| ルール | 内容 |
|---|---|
| BR-02-1 | `date` パラメータのデフォルト値は `"today"` |
| BR-02-2 | `date` と `period` が両方指定された場合、`period` を優先する |
| BR-02-3 | `period` に指定できる値は `"7d"`, `"30d"`, `"1m"`, `"3m"`, `"6m"`, `"1y"` のみ |
| BR-02-4 | `date` に指定できる書式は `"today"` または `"YYYY-MM-DD"` 形式のみ |

---

## BR-03: Fitbit API エラー処理

| ルール | 内容 |
|---|---|
| BR-03-1 | すべての Fitbit API エラーは**文字列として**ツールの戻り値で返す |
| BR-03-2 | エラー文字列の形式: `"Error {status_code}: {description}"` |
| BR-03-3 | HTTP 401（認証切れ）: `"Error 401: アクセストークンが無効です。再認証が必要です。"` |
| BR-03-4 | HTTP 429（レート制限）: `"Error 429: APIリクエスト上限に達しました。しばらく待ってから再試行してください。"` |
| BR-03-5 | HTTP 404（データなし）: `"Error 404: 指定期間のデータが見つかりません。"` |
| BR-03-6 | ネットワークエラー: `"Error Network: Fitbit APIへの接続に失敗しました。"` |
| BR-03-7 | エラー文字列の伝達は LLM が担当し、ユーザーに自然言語で通知する |

---

## BR-04: トークン管理

| ルール | 内容 |
|---|---|
| BR-04-1 | アクセストークンの有効期限まで **5分以内**の場合、事前にリフレッシュを実行する |
| BR-04-2 | リフレッシュトークンが無効な場合、エラーを返し再認証をユーザーに案内する |
| BR-04-3 | Unit 1 開発時は `.env` ファイルにトークンを手動設定して動作確認する |

---

## BR-05: Long-term Memory 保存

| ルール | 内容 |
|---|---|
| BR-05-1 | Long-term memory の保存は**毎ターンの応答後**に `memory_save_node` が実行する |
| BR-05-2 | 保存する情報は LLM が会話全体から**要約・抽出**したテキスト |
| BR-05-3 | 同一 `session_id` のメモリを上書き更新する（重複保存しない） |
| BR-05-4 | 取得時は **コサイン類似度** による意味的検索で上位 3 件を取得する |
| BR-05-5 | 取得したメモリは `memory_inject_node` でシステムプロンプトの先頭に注入する |

---

## BR-06: AgentState の構成

| ルール | 内容 |
|---|---|
| BR-06-1 | `AgentState` は `messages`（LangGraph MessagesState）と `session_id`（str）のみ保持する |
| BR-06-2 | ユーザーの目標体重・ペースは `messages` の履歴から LLM が参照する |
| BR-06-3 | `fitbit_cache` は実装しない（シンプルさを優先） |

---

## BR-07: 食事データ補完

| ルール | 内容 |
|---|---|
| BR-07-1 | `get_calories_in` がデータなし（null または 0）を返した場合、LLM がユーザーに食事内容を質問する |
| BR-07-2 | ユーザーが食事内容を自然言語で伝えた場合、LLM が概算カロリーを計算して提示する |
| BR-07-3 | LLM が計算したカロリーは推定値であり、その旨をユーザーに伝える |

---

## BR-08: 自宅運動プラン生成

| ルール | 内容 |
|---|---|
| BR-08-1 | 生成する運動プランは**器具不要の自宅運動のみ**（ジム種目を含めない） |
| BR-08-2 | プランには週次スケジュール・各日のメニュー・フォームの注意点を含める |
| BR-08-3 | フィットネスレベル（`beginner` / `intermediate` / `advanced`）に合わせた種目を提案する |

---

## BR-09: PBT テスト可能プロパティ（Property-Based Testing）

Property-Based Testing (Hypothesis) での検証対象プロパティ。

### PBT-09-1: カロリー赤字計算の不変条件
```
PROPERTY: calculate_calorie_deficit の出力は常に安全範囲内
  GIVEN: any valid (current_weight, target_weight, pace)
  THEN:
    - daily_deficit_kcal が 200〜1000 の範囲内
    - total_loss_kg が正の値
    - weeks_to_goal が正の値
    - pace_kg_per_week が 0.1〜1.0 の範囲内
```

### PBT-09-2: 週次進捗の単調性
```
PROPERTY: 体重が減少するにつれて progress_ratio は増加する
  GIVEN: 同一の start_weight と target_pace で current_weight を変化させる
  THEN: current_weight が小さいほど progress_ratio が大きい（または同じ）
```

### PBT-09-3: カロリー計算の逆算
```
PROPERTY: pace から daily_deficit を計算し、daily_deficit × 7 / 7200 = pace
  GIVEN: any valid pace_kg_per_week
  THEN: (daily_deficit_kcal × 7) / 7200 ≈ pace_kg_per_week（誤差 0.01 以内）
```

### PBT-09-4: 日付パラメータの排他性
```
PROPERTY: period が指定された場合、date は無視される
  GIVEN: any (date, period) combination
  THEN: period が指定されていれば get_fitbit_data は period を使用する
```
