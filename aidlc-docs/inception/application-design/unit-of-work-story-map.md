# Unit of Work Story Map — Fitbit Weight Management AI Agent

## ストーリーマッピング

| US# | ストーリー | ユニット | 優先度 |
|-----|-----------|---------|-------|
| US-14 | ショートタームメモリ（MemorySaver） | Unit 1: AI Agent Core | 高 |
| US-04 | 活動量データ取得（get_steps / get_calories_burned） | Unit 1: AI Agent Core | 高 |
| US-05 | 体重・BMI取得（get_weight） | Unit 1: AI Agent Core | 高 |
| US-06 | 心拍数取得（get_heart_rate） | Unit 1: AI Agent Core | 中 |
| US-07 | 食事ログ取得（get_calories_in） | Unit 1: AI Agent Core | 高 |
| US-09 | チャットによる食事データ補完 | Unit 1: AI Agent Core | 高 |
| US-10 | 目標体重プラン生成（calculate_calorie_deficit） | Unit 1: AI Agent Core | 高 |
| US-11 | 食事プランの提案 | Unit 1: AI Agent Core | 高 |
| US-12 | 自宅運動プランの提案（generate_home_workout_plan） | Unit 1: AI Agent Core | 高 |
| US-13 | 進捗確認（get_weekly_progress） | Unit 1: AI Agent Core | 中 |
| US-15 | ロングタームメモリ（pgvector セマンティックメモリ） | Unit 1: AI Agent Core | 中 |
| US-02 | トークン自動リフレッシュ（_get_valid_token） | Unit 1: AI Agent Core | 高 |
| US-01 | Fitbit OAuth2 認証フロー | Unit 2: Backend API | 高 |
| US-08 | 自然言語チャット（API エンドポイント側） | Unit 2: Backend API | 高 |
| US-03 | 連携状態の確認（API 側） | Unit 2: Backend API | 中 |
| US-08 | 自然言語チャット（UI 側） | Unit 3: Frontend | 高 |
| US-03 | 連携状態の確認（UI 表示側） | Unit 3: Frontend | 中 |

---

## Unit 別ストーリー一覧

### Unit 1: AI Agent Core（11ストーリー）

| US# | ストーリー | 実装コンポーネント |
|-----|-----------|----------------|
| US-02 | トークン自動リフレッシュ | FitbitClient.`_get_valid_token()` |
| US-04 | 活動量データ取得 | `get_steps`, `get_calories_burned` @tool + FitbitClient |
| US-05 | 体重・BMI取得 | `get_weight` @tool + FitbitClient |
| US-06 | 心拍数取得 | `get_heart_rate` @tool + FitbitClient |
| US-07 | 食事ログ取得 | `get_calories_in` @tool + FitbitClient |
| US-09 | チャット食事データ補完 | agent_node（LLM 判断ロジック） |
| US-10 | 目標体重プラン生成 | `calculate_calorie_deficit` @tool |
| US-11 | 食事プラン提案 | agent_node（LLM 生成） |
| US-12 | 自宅運動プラン提案 | `generate_home_workout_plan` @tool |
| US-13 | 進捗確認 | `get_weekly_progress` @tool + FitbitClient |
| US-14 | ショートタームメモリ | MemorySaver + MessagesState |
| US-15 | ロングタームメモリ | MemoryManager + pgvector |

### Unit 2: Backend API（4ストーリー）

| US# | ストーリー | 実装コンポーネント |
|-----|-----------|----------------|
| US-01 | Fitbit OAuth2 認証フロー | FitbitService + FitbitClient（OAuth2メソッド追記）+ `/auth/fitbit` |
| US-03 | 連携状態確認（API） | `GET /health` + 認証状態レスポンス |
| US-08 | 自然言語チャット（API） | `POST /chat`（SSE）+ LangGraphAgent 呼び出し |

### Unit 3: Frontend（2ストーリー）

| US# | ストーリー | 実装コンポーネント |
|-----|-----------|----------------|
| US-08 | 自然言語チャット（UI） | ChatUI + SSE クライアント |
| US-03 | 連携状態確認（UI） | Fitbit 接続ステータス表示 + 認証ボタン |

---

## カバレッジ確認

- **全15ストーリー**: すべてのユニットにマッピング済み ✓
- **US-03, US-08**: Frontend と Backend API にまたがるため両ユニットにマッピング ✓
