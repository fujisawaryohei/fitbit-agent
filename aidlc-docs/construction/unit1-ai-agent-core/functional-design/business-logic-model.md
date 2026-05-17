# Business Logic Model — Unit 1: AI Agent Core

## 対象ストーリー
US-02, US-04〜07, US-09〜15

---

## BLM-01: カロリー赤字計算（US-10）

### 入力
| パラメータ | 型 | 説明 |
|---|---|---|
| `current_weight_kg` | float | 現在の体重（kg） |
| `target_weight_kg` | float | 目標体重（kg） |
| `pace_kg_per_week` | float | 週あたりの減量ペース（デフォルト: 0.5） |

### アルゴリズム

```
FUNCTION calculate_calorie_deficit(current_weight_kg, target_weight_kg, pace_kg_per_week=0.5):

  1. total_loss_kg = current_weight_kg - target_weight_kg
     IF total_loss_kg <= 0: RETURN error("目標体重は現在体重より軽くしてください")

  2. KCAL_PER_KG = 7200  # 体重1kg減 = 7,200kcal の法則
     weekly_deficit_kcal = pace_kg_per_week × KCAL_PER_KG
     daily_deficit_kcal = weekly_deficit_kcal / 7

  3. weeks_to_goal = total_loss_kg / pace_kg_per_week
     days_to_goal = weeks_to_goal × 7

  4. RETURN {
       daily_deficit_kcal: round(daily_deficit_kcal),
       weeks_to_goal: round(weeks_to_goal, 1),
       total_loss_kg: round(total_loss_kg, 1),
       pace_kg_per_week: pace_kg_per_week
     }
```

### デフォルト動作
- `pace_kg_per_week` のデフォルト値は **0.5 kg/週**
- ユーザーが「週1kg落としたい」と指定した場合、LLM が `pace_kg_per_week=1.0` を渡す

### 安全制約
- 最大ペース: `pace_kg_per_week <= 1.0`（急激な減量は健康リスクがあるため）
- 最小 daily_deficit: `200kcal`、最大: `1000kcal`

---

## BLM-02: 自宅運動プラン生成（US-12）

### 方式
**LLM 完全委任** — `generate_home_workout_plan` ツールが LLM に対して構造化プロンプトを送り、プランを生成させる

### 入力
| パラメータ | 型 | 説明 |
|---|---|---|
| `daily_deficit_kcal` | int | 1日の目標カロリー赤字 |
| `fitness_level` | str | "beginner" / "intermediate" / "advanced" |
| `available_days_per_week` | int | 週の運動可能日数（1〜7） |
| `duration_minutes` | int | 1回の運動時間（分） |

### アルゴリズム

```
FUNCTION generate_home_workout_plan(daily_deficit_kcal, fitness_level, 
                                     available_days_per_week, duration_minutes):

  1. prompt = build_workout_prompt(
       daily_deficit_kcal, fitness_level, 
       available_days_per_week, duration_minutes
     )
     # プロンプト要素:
     # - 目標カロリー消費量（daily_deficit_kcal の一部を運動で補う）
     # - フィットネスレベルに合わせた種目選択
     # - 自宅でできる種目のみ（器具不要）
     # - 週次スケジュール + 各日のメニュー + フォーム説明

  2. plan_text = LLM.invoke(prompt)

  3. RETURN plan_text
```

### LLM に要求するプラン構造
1. 週次スケジュール（例: 月・水・金トレーニング、火・木・土休息）
2. 各日のメニュー（種目名、セット数、回数または時間）
3. フォームのポイント（各種目の注意事項）
4. 推定カロリー消費量

---

## BLM-03: 食事データ補完（US-09）

### 課題
Fitbit の食事ログは **ユーザーが手動入力** する必要がある。未入力の場合はデータなし（null）。

### アルゴリズム

```
FUNCTION handle_missing_food_log(food_log_result):

  1. IF food_log_result is None OR food_log_result.calories == 0:
       RETURN prompt_user_for_food_log()
       # エージェントが「今日の食事を教えてください」とユーザーに質問

  2. ELSE:
       RETURN food_log_result
```

### エージェントの振る舞い
- `get_calories_in` ツールがデータなしを返した場合、`agent_node`（LLM）がユーザーに食事を尋ねる
- ユーザーが食事内容をチャットで伝えると、LLM が概算カロリーを計算して提案

---

## BLM-04: 週次進捗確認（US-13）

### 入力
| パラメータ | 型 | 説明 |
|---|---|---|
| `current_weight_kg` | float | 現在の体重 |
| `start_weight_kg` | float | 開始時の体重 |
| `target_pace_kg_per_week` | float | 目標週次ペース |
| `weeks_elapsed` | int | 経過週数 |

### アルゴリズム

```
FUNCTION get_weekly_progress(current_weight_kg, start_weight_kg, 
                               target_pace_kg_per_week, weeks_elapsed):

  1. actual_loss_kg = start_weight_kg - current_weight_kg
  2. expected_loss_kg = target_pace_kg_per_week × weeks_elapsed
  3. progress_ratio = actual_loss_kg / expected_loss_kg IF expected_loss_kg > 0 ELSE 0

  4. status = 
       IF progress_ratio >= 0.9: "順調"
       IF progress_ratio >= 0.5: "やや遅れ"
       ELSE: "遅れ気味"

  5. RETURN {
       actual_loss_kg: round(actual_loss_kg, 1),
       expected_loss_kg: round(expected_loss_kg, 1),
       progress_ratio: round(progress_ratio, 2),
       status: status
     }
```

---

## BLM-05: Long-term Memory の保存と取得（US-15）

### 保存タイミング
**毎ターン（会話応答後）** — `memory_save_node` が各ターン末尾で実行される

### 保存アルゴリズム

```
FUNCTION save_long_term_memory(messages, session_id):

  1. summary_prompt = "以下の会話から、ユーザーの目標・好み・重要情報を
                       日本語で簡潔に要約してください:\n{messages}"
  2. summary_text = LLM.invoke(summary_prompt)

  3. embedding = VectorStore.embed(summary_text)

  4. VectorStore.upsert(
       content=summary_text,
       embedding=embedding,
       session_id=session_id,
       timestamp=now()
     )
```

### 取得アルゴリズム（会話開始時）

```
FUNCTION load_long_term_memory(session_id, current_message):

  1. query_embedding = VectorStore.embed(current_message)

  2. relevant_memories = VectorStore.similarity_search(
       embedding=query_embedding,
       limit=3,
       filter={"session_id": session_id}  # 同一ユーザーのみ
     )

  3. memory_context = format_memories(relevant_memories)

  4. RETURN memory_context  # agent_node のシステムプロンプトに注入
```

---

## BLM-06: トークン自動リフレッシュ（US-02）

### アルゴリズム

```
FUNCTION _get_valid_token(session_id):

  1. token_data = TokenStore.get(session_id)
     IF token_data is None: RAISE TokenNotFoundError

  2. IF token_data.expires_at <= now() + timedelta(minutes=5):
       # 期限切れ or 5分以内に切れる場合はリフレッシュ
       new_token = FitbitAPI.refresh_token(token_data.refresh_token)
       TokenStore.save(session_id, new_token)
       RETURN new_token.access_token

  3. RETURN token_data.access_token
```

---

## BLM-07: Fitbit API データ取得（US-04〜07）

### 共通パターン（全データ取得メソッド）

```
FUNCTION get_fitbit_data(endpoint, date="today", period=None):

  1. access_token = _get_valid_token()

  2. url = build_url(endpoint, date, period)

  3. response = HTTP.GET(url, headers={"Authorization": f"Bearer {access_token}"})

  4. IF response.status == 200:
       RETURN parse_response(response.json())
  
  5. ELSE:
       RETURN f"Error {response.status}: {response.text}"
       # LLM がユーザーに自然言語で伝える（Q6: A）
```

### 日付パラメータ仕様（Q5: C）
| パラメータ | 型 | 例 | 説明 |
|---|---|---|---|
| `date` | str | `"today"`, `"2026-05-17"` | 特定日付のデータ |
| `period` | str | `"7d"`, `"30d"`, `"1m"` | 期間集計データ |
- `date` と `period` は排他的。両方指定された場合は `period` を優先

---

## BLM-08: LangGraph グラフ実行フロー

```
START
  │
  ▼
memory_inject_node
  │ Long-term memory を取得してシステムプロンプトに注入
  ▼
agent_node (LLM)
  │ メッセージ履歴 + メモリから応答・ツール呼び出し判断
  │
  ├─── ツール呼び出しあり ──→ tool_node ──→ (agent_node へループ)
  │
  └─── 最終回答 ──→ memory_save_node
                       │ 会話を要約して pgvector に保存
                       ▼
                     END
```
