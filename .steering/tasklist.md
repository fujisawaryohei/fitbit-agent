# TODO: Fitbit Body Management AI Agent

> PMであるClaudeがチケットを管理するファイル。
> ステータス: `[ ]` 未着手 / `[>]` 進行中 / `[x]` 完了

---

## Phase 0: プロジェクトセットアップ

### TASK-001: Spring Boot プロジェクト初期化
- **優先度**: 高
- **機能ID**: -
- **概要**: backend/ に Spring Boot 3.x + Maven プロジェクトを生成する
- **受入条件**:
  - [ ] `backend/pom.xml` に必要な依存関係が定義されている
  - [ ] `mvn compile` が成功する
  - [ ] パッケージ構成が docs/architecture.md に準拠している
- **ステータス**: `[x]`
- **parallel-group**: 0-A
- **影響ファイル**: `backend/`

### TASK-002: React プロジェクト初期化
- **優先度**: 高
- **機能ID**: -
- **概要**: frontend/ に React + TypeScript + Vite プロジェクトを生成する
- **受入条件**:
  - [ ] `frontend/package.json` に必要な依存関係が定義されている
  - [ ] `npm run build` が成功する
  - [ ] ディレクトリ構成が docs/repository-structure.md に準拠している
- **ステータス**: `[ ]`
- **parallel-group**: 0-A
- **影響ファイル**: `frontend/`

### TASK-003: Docker Compose ローカル開発環境構築
- **優先度**: 高
- **機能ID**: -
- **概要**: docker/docker-compose.yml で PostgreSQL + Spring Boot のローカル環境を構築する
- **受入条件**:
  - [ ] `docker compose up` でPostgreSQLが起動する
  - [ ] Spring BootからPostgreSQLに接続できる
- **ステータス**: `[x]`
- **ブロック**: TASK-001
- **parallel-group**: -
- **影響ファイル**: `docker/`, `backend/src/main/resources/`

### TASK-004: Flyway DBマイグレーション初期設定
- **優先度**: 高
- **機能ID**: -
- **概要**: 基本設計書のデータモデルに基づき、Flywayマイグレーションファイルを作成する
- **受入条件**:
  - [x] 全テーブル（users, oauth_tokens, body_records, activity_records, sleep_records, nutrition_records, heart_rate_records, goals, ai_advices, chat_messages）が作成される
  - [x] インデックスが設計通りに作成される
  - [x] `mvn flyway:migrate` が成功する
- **ステータス**: `[x]`
- **ブロック**: TASK-003
- **parallel-group**: -
- **影響ファイル**: `backend/src/main/resources/db/migration/`

### TASK-005: GitHub Actions CI パイプライン構築
- **優先度**: 中
- **機能ID**: -
- **概要**: PR時のテスト実行、main マージ時のビルドを自動化する
- **受入条件**:
  - [ ] PRでバックエンド・フロントエンドのテストが自動実行される
  - [ ] テスト失敗時にPRでステータスが表示される
- **ステータス**: `[ ]`
- **parallel-group**: 0-A
- **影響ファイル**: `.github/workflows/`

---

## Phase 1: 認証・ユーザー管理

### TASK-010: Fitbit OAuth2.0 ログイン（バックエンド）
- **優先度**: 高
- **機能ID**: FR-001
- **概要**: Spring Security + OAuth2 Client で Fitbit OAuth2.0 認証を実装する
- **受入条件**:
  - [ ] `GET /api/auth/login` でFitbit認可URLにリダイレクトされる
  - [ ] `GET /api/auth/callback` でトークン取得・暗号化保存・セッション生成が行われる
  - [ ] トークン自動リフレッシュが動作する
- **ステータス**: `[x]`
- **ブロック**: TASK-001, TASK-004
- **parallel-group**: -
- **影響ファイル**: `backend/src/main/java/.../auth/`, `backend/src/main/java/.../security/`

### TASK-010T: 認証・トークン暗号化 単体テスト
- **優先度**: 高
- **機能ID**: FR-001
- **概要**: TASK-010 で実装した AuthService / TokenEncryptionService の Spock 単体テストを作成する
- **受入条件**:
  - [x] `TokenEncryptionService` の暗号化・復号化テストが通る
  - [x] `AuthService.buildAuthorizationUrl()` のテストが通る
  - [x] `AuthService.handleCallback()` のテストが通る（FitbitOAuthClient をモック）
  - [x] `AuthService.refreshToken()` のテストが通る
  - [x] `mvn test` が成功する
- **ステータス**: `[x]`
- **ブロック**: TASK-010
- **parallel-group**: 1-A
- **影響ファイル**: `backend/src/test/groovy/.../auth/`

### TASK-011: ログイン画面（フロントエンド）
- **優先度**: 高
- **機能ID**: FR-001, SCR-001
- **概要**: Fitbitログインボタンを持つログイン画面を実装する
- **受入条件**:
  - [ ] `/login` にログインボタンが表示される
  - [ ] ボタン押下でFitbit認可画面に遷移する
  - [ ] 認証成功後に `/dashboard` にリダイレクトされる
- **ステータス**: `[ ]`
- **ブロック**: TASK-002, TASK-010
- **parallel-group**: -
- **影響ファイル**: `frontend/src/pages/login/`, `frontend/src/components/`

### TASK-012: ユーザープロフィール管理（バックエンド）
- **優先度**: 中
- **機能ID**: FR-002
- **概要**: プロフィール取得・編集APIを実装する
- **受入条件**:
  - [x] `GET /api/users/me` で現在のプロフィールが返却される
  - [x] `PUT /api/users/me` でプロフィールが更新される
  - [x] 初回ログイン時にFitbit APIからプロフィールが自動取得される
- **ステータス**: `[x]`
- **ブロック**: TASK-010
- **parallel-group**: 1-A
- **影響ファイル**: `backend/src/main/java/.../user/`

### TASK-012T: ユーザープロフィール管理 単体テスト
- **優先度**: 中
- **機能ID**: FR-002
- **概要**: TASK-012 で実装した ProfileService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] `GET /api/users/me` のAPIテストが通る
  - [ ] `PUT /api/users/me` のAPIテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-012
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../user/`

### TASK-013: ログアウト
- **優先度**: 中
- **機能ID**: FR-003
- **概要**: ログアウトAPIとフロントエンドのログアウト処理を実装する
- **受入条件**:
  - [x] `POST /api/auth/logout` でセッションが破棄される
  - [x] ログアウト後にログイン画面にリダイレクトされる
  - [x] 未認証で保護画面にアクセスするとログイン画面に遷移する
- **ステータス**: `[x]`
- **ブロック**: TASK-010
- **parallel-group**: 1-A
- **影響ファイル**: `backend/src/main/java/.../auth/`, `frontend/src/`

---

## Phase 2: Fitbit データ連携

### TASK-020: Fitbit APIクライアント実装
- **優先度**: 高
- **機能ID**: FR-010
- **概要**: FitbitApiClient / FitbitRateLimiter を実装する
- **受入条件**:
  - [ ] 各データ種別（body, activity, sleep, nutrition, heart_rate）のAPI呼び出しが動作する
  - [ ] レート制限カウンターが正しく動作する（安全マージン145で停止）
  - [ ] 401応答時にトークンリフレッシュ→リトライが行われる
- **ステータス**: `[ ]`
- **ブロック**: TASK-010
- **parallel-group**: -
- **影響ファイル**: `backend/src/main/java/.../fitbit/`

### TASK-020T: Fitbit APIクライアント 単体テスト
- **優先度**: 高
- **機能ID**: FR-010
- **概要**: TASK-020 で実装した FitbitApiClient / FitbitRateLimiter の Spock 単体テストを作成する
- **受入条件**:
  - [ ] 各データ種別の API 呼び出しテストが通る（WebClient をモック）
  - [ ] レート制限カウンターのテストが通る（145件で停止）
  - [ ] 401応答時のリトライテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-020
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../fitbit/`

### TASK-021: データ同期サービス実装
- **優先度**: 高
- **機能ID**: FR-010, FR-011
- **概要**: SyncService / SyncController を実装する
- **受入条件**:
  - [ ] `POST /api/sync` で全データ種別が並列取得・DB保存される
  - [ ] 初回同期時は過去90日分を取得する
  - [ ] 差分同期（前回同期日以降）が動作する
  - [ ] 部分同期（一部失敗時）でエラーが返却される
- **ステータス**: `[ ]`
- **ブロック**: TASK-020
- **parallel-group**: -
- **影響ファイル**: `backend/src/main/java/.../sync/`

### TASK-021T: データ同期サービス 単体テスト
- **優先度**: 高
- **機能ID**: FR-010, FR-011
- **概要**: TASK-021 で実装した SyncService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] 初回同期（過去90日分）のテストが通る
  - [ ] 差分同期のテストが通る
  - [ ] 部分同期エラー時のテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-021
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../sync/`

---

## Phase 3: ダッシュボード

### TASK-030: ダッシュボードAPI実装（バックエンド）
- **優先度**: 高
- **機能ID**: FR-020, FR-021, FR-022
- **概要**: DashboardService / DashboardController を実装する
- **受入条件**:
  - [ ] `GET /api/dashboard/summary` で当日のサマリーデータが返却される
  - [ ] `GET /api/dashboard/charts/{type}` で指定期間のグラフデータが返却される
  - [ ] `GET /api/dashboard/progress` で目標進捗が返却される
- **ステータス**: `[ ]`
- **ブロック**: TASK-021
- **parallel-group**: 3-A
- **影響ファイル**: `backend/src/main/java/.../dashboard/`

### TASK-030T: ダッシュボードAPI 単体テスト
- **優先度**: 高
- **機能ID**: FR-020, FR-021, FR-022
- **概要**: TASK-030 で実装した DashboardService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] `GET /api/dashboard/summary` のAPIテストが通る
  - [ ] `GET /api/dashboard/charts/{type}` のAPIテストが通る
  - [ ] `GET /api/dashboard/progress` のAPIテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-030
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../dashboard/`

### TASK-031: ダッシュボード画面（フロントエンド）
- **優先度**: 高
- **機能ID**: FR-020, FR-021, FR-022, SCR-002
- **概要**: サマリーカード・推移グラフ・目標進捗をダッシュボード画面に実装する
- **受入条件**:
  - [ ] サマリーカードに体重・歩数・カロリー・睡眠が表示される
  - [ ] データ未登録時は「--」が表示される
  - [ ] 推移グラフが表示され、期間切替が動作する
  - [ ] 目標進捗のプログレスバーが表示される
- **ステータス**: `[ ]`
- **ブロック**: TASK-030
- **parallel-group**: 3-A
- **影響ファイル**: `frontend/src/pages/dashboard/`

### TASK-032: グラフ詳細画面（フロントエンド）
- **優先度**: 中
- **機能ID**: FR-021, SCR-003
- **概要**: 各指標の詳細グラフ画面を実装する
- **受入条件**:
  - [ ] `/dashboard/charts/:type` で各指標の詳細グラフが表示される
  - [ ] 1週間/1ヶ月/3ヶ月/カスタム期間の切替が動作する
  - [ ] ツールチップで詳細値が表示される
- **ステータス**: `[ ]`
- **ブロック**: TASK-031
- **parallel-group**: -
- **影響ファイル**: `frontend/src/pages/dashboard/charts/`

---

## Phase 4: 目標設定

### TASK-040: 目標管理API実装（バックエンド）
- **優先度**: 高
- **機能ID**: FR-030, FR-031
- **概要**: GoalService / GoalController を実装する
- **受入条件**:
  - [ ] 目標のCRUD (GET/POST/PUT/DELETE /api/goals) が動作する
  - [ ] 体重目標の減量ペースバリデーション（0.5〜1.0kg/週）が動作する
  - [ ] 過度な目標設定時に警告レスポンスが返却される
- **ステータス**: `[ ]`
- **ブロック**: TASK-004
- **parallel-group**: 4-A
- **影響ファイル**: `backend/src/main/java/.../goal/`

### TASK-040T: 目標管理API 単体テスト
- **優先度**: 高
- **機能ID**: FR-030, FR-031
- **概要**: TASK-040 で実装した GoalService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] 目標 CRUD のAPIテストが通る
  - [ ] 減量ペースバリデーションのテストが通る（0.5〜1.0kg/週の境界値テスト含む）
  - [ ] 過度な目標設定時の警告テストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-040
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../goal/`

### TASK-041: 目標設定画面（フロントエンド）
- **優先度**: 高
- **機能ID**: FR-030, FR-031, SCR-004
- **概要**: 体重目標・日次活動目標の設定フォームを実装する
- **受入条件**:
  - [ ] 目標体重・達成期限を入力・保存できる
  - [ ] 日次目標（歩数・カロリー）を入力・保存できる
  - [ ] 過度な目標時に警告ダイアログが表示される
  - [ ] 既存目標の変更・削除ができる
- **ステータス**: `[ ]`
- **ブロック**: TASK-040
- **parallel-group**: -
- **影響ファイル**: `frontend/src/pages/goal/`

---

## Phase 5: AIコーチング

### TASK-050: Claude APIクライアント実装
- **優先度**: 高
- **機能ID**: FR-040, FR-041, FR-042
- **概要**: ClaudeApiClient / PromptBuilder を実装する
- **受入条件**:
  - [ ] Claude API呼び出し（非ストリーミング）が動作する
  - [ ] Claude API呼び出し（ストリーミング）が動作する
  - [ ] リトライ（指数バックオフ）が動作する
  - [ ] プロンプトテンプレートの変数埋め込みが動作する
- **ステータス**: `[ ]`
- **ブロック**: TASK-001
- **parallel-group**: 5-A
- **影響ファイル**: `backend/src/main/java/.../claude/`

### TASK-050T: Claude APIクライアント 単体テスト
- **優先度**: 高
- **機能ID**: FR-040, FR-041, FR-042
- **概要**: TASK-050 で実装した ClaudeApiClient / PromptBuilder の Spock 単体テストを作成する
- **受入条件**:
  - [ ] 非ストリーミング API 呼び出しテストが通る（Claude API をモック）
  - [ ] ストリーミング API 呼び出しテストが通る
  - [ ] リトライ（指数バックオフ）のテストが通る
  - [ ] プロンプトテンプレートの変数埋め込みテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-050
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../claude/`

### TASK-051: 日次アドバイス生成（バックエンド）
- **優先度**: 高
- **機能ID**: FR-040
- **概要**: AdviceService / AdviceController の日次アドバイス機能を実装する
- **受入条件**:
  - [ ] `POST /api/advice/daily` でAIアドバイスが生成・保存される
  - [ ] プロンプトにユーザーのヘルスデータ・目標・7日間トレンドが含まれる
  - [ ] `GET /api/advice/daily/{date}` で保存済みアドバイスが取得できる
- **ステータス**: `[ ]`
- **ブロック**: TASK-050, TASK-021
- **parallel-group**: 5-B
- **影響ファイル**: `backend/src/main/java/.../advice/`

### TASK-051T: 日次アドバイス生成 単体テスト
- **優先度**: 高
- **機能ID**: FR-040
- **概要**: TASK-051 で実装した AdviceService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] `POST /api/advice/daily` のAPIテストが通る（ClaudeApiClient をモック）
  - [ ] プロンプトにヘルスデータ・目標・7日間トレンドが含まれるテストが通る
  - [ ] `GET /api/advice/daily/{date}` のAPIテストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-051
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../advice/`

### TASK-052: 日次アドバイス表示（フロントエンド）
- **優先度**: 高
- **機能ID**: FR-040, SCR-002
- **概要**: ダッシュボードにAIアドバイスカードを追加する
- **受入条件**:
  - [ ] ダッシュボードにアドバイスカードが表示される
  - [ ] 再生成ボタンでアドバイスを更新できる
- **ステータス**: `[ ]`
- **ブロック**: TASK-051, TASK-031
- **parallel-group**: -
- **影響ファイル**: `frontend/src/pages/dashboard/`, `frontend/src/components/advice/`

### TASK-053: 週次レポート生成
- **優先度**: 中
- **機能ID**: FR-041
- **概要**: 週次レポートの生成API・表示画面を実装する
- **受入条件**:
  - [ ] `POST /api/advice/weekly` で週次レポートが生成・保存される
  - [ ] `GET /api/advice/weekly` で過去の週次レポート一覧が取得できる
  - [ ] SCR-006 で週次レポートが閲覧できる
- **ステータス**: `[ ]`
- **ブロック**: TASK-051
- **parallel-group**: 5-B
- **影響ファイル**: `backend/src/main/java/.../advice/`, `frontend/src/pages/report/`

### TASK-054: チャットコーチング（バックエンド）
- **優先度**: 中
- **機能ID**: FR-042
- **概要**: ChatService / ChatController（SSEストリーミング）を実装する
- **受入条件**:
  - [ ] `POST /api/chat/messages` でSSEストリーミング応答が返却される
  - [ ] 会話履歴がDBに保存される
  - [ ] プロンプトにヘルスデータ・会話履歴が含まれる
- **ステータス**: `[ ]`
- **ブロック**: TASK-050
- **parallel-group**: 5-B
- **影響ファイル**: `backend/src/main/java/.../chat/`

### TASK-054T: チャットコーチング 単体テスト
- **優先度**: 中
- **機能ID**: FR-042
- **概要**: TASK-054 で実装した ChatService の Spock 単体テストを作成する
- **受入条件**:
  - [ ] SSEストリーミング応答のAPIテストが通る
  - [ ] 会話履歴の保存・取得テストが通る
  - [ ] `mvn test` が成功する
- **ステータス**: `[ ]`
- **ブロック**: TASK-054
- **parallel-group**: -
- **影響ファイル**: `backend/src/test/groovy/.../chat/`

### TASK-055: チャット画面（フロントエンド）
- **優先度**: 中
- **機能ID**: FR-042, SCR-005
- **概要**: AIコーチとのチャットUIを実装する
- **受入条件**:
  - [ ] メッセージを入力・送信できる
  - [ ] AIの応答がストリーミングでリアルタイム表示される
  - [ ] 会話の文脈が維持される
- **ステータス**: `[ ]`
- **ブロック**: TASK-054
- **parallel-group**: -
- **影響ファイル**: `frontend/src/pages/chat/`

---

## Phase 6: プロフィール・設定

### TASK-060: プロフィール画面（フロントエンド）
- **優先度**: 低
- **機能ID**: FR-002, SCR-007
- **概要**: ユーザー情報編集画面を実装する
- **受入条件**:
  - [ ] プロフィール情報が表示・編集・保存できる
- **ステータス**: `[ ]`
- **ブロック**: TASK-012
- **parallel-group**: 6-A
- **影響ファイル**: `frontend/src/pages/profile/`

### TASK-061: 設定画面（フロントエンド）
- **優先度**: 低
- **機能ID**: SCR-008
- **概要**: データ管理・アカウント設定画面を実装する
- **受入条件**:
  - [ ] 手動同期ボタンが動作する
  - [ ] ログアウトボタンが動作する
- **ステータス**: `[ ]`
- **ブロック**: TASK-013, TASK-021
- **parallel-group**: 6-A
- **影響ファイル**: `frontend/src/pages/settings/`

---

## Phase 7: 共通UI・レイアウト

### TASK-070: 共通レイアウト実装（フロントエンド）
- **優先度**: 高
- **機能ID**: -
- **概要**: Header / BottomNav / AuthLayout を実装する
- **受入条件**:
  - [ ] 認証済み画面にヘッダー・ナビゲーションが表示される
  - [ ] モバイルでボトムナビゲーションが表示される
  - [ ] 未認証時にログイン画面へリダイレクトされる
- **ステータス**: `[ ]`
- **ブロック**: TASK-002
- **parallel-group**: -
- **影響ファイル**: `frontend/src/components/layout/`, `frontend/src/router/`

---

## 並列グループ一覧

| グループ | タスク | 条件 |
|---|---|---|
| **0-A** | TASK-001, TASK-002, TASK-005 | 同時実行可（依存なし） |
| **1-A** | TASK-010T, TASK-012, TASK-013 | TASK-010完了後に同時実行可 |
| **3-A** | TASK-030, TASK-031 | TASK-021完了後・影響ファイル分離 |
| **4-A** | TASK-040（Phase 2〜3と並列可） | TASK-004完了後・影響ファイル分離 |
| **5-A** | TASK-050（Phase 2と並列可） | TASK-001完了後・影響ファイル分離 |
| **5-B** | TASK-051, TASK-053, TASK-054 | TASK-050T完了後に同時実行可 |
| **6-A** | TASK-060, TASK-061 | 各ブロック解消後・影響ファイル分離 |

---

## 更新履歴
- 2026-02-09: 初版作成（MVP全チケット起票）
- 2026-02-28: テストタスク追加（TASK-010T〜054T）
- 2026-03-15: 並列開発対応（parallel-group・影響ファイルフィールド追加、並列グループ一覧追加）
