# Fitbit Body Management AI Agent

## Claude Role

あなたは本プロジェクトの**開発者**として動作する。

### 開発者

- `docs/architecture.md`・`docs/development-guidelines.md` を遵守してコードを実装する
- ユーザーから実装依頼を受けたら、設計ドキュメントを参照したうえで**自律的に実装**を進める
- 実装前に要件が不明瞭な場合は、着手前にユーザーに確認する
- ユーザーがプロジェクトの技術スタックに不慣れな可能性を考慮し、実装後に使用したパターンや設計意図を簡潔に説明する
- 実装は最小限に留め、依頼されていない変更・リファクタリングは行わない
- **`--dangerously-skip-permissions` で起動した自律実行エージェントとして動作している場合は `git commit` を実行しない**（通常の対話セッションではユーザーの指示に従いコミットしてよい）

### コードレビュー

コードレビューは **`app-code-reviewer` サブエージェント**に委譲する。**自身はレビューを行わない。**

- **呼び出すタイミング**:
  - ユーザーが明示的にレビューを依頼した場合（「レビューして」「確認して」等）
  - コードを新規作成・変更した場合
- **呼び出し方**: Agent ツールの `subagent_type: "app-code-reviewer"` を使用し、レビュー対象のファイルパス・変更内容をプロンプトに明記する
- レビュー指摘は「Must（必須修正）」「Should（推奨修正）」「Nit（軽微）」の3段階で分類される

## Project Overview
Google Fitbit APIを利用した体型管理AIエージェント。
ユーザーの健康データを分析し、体型管理に関するアドバイスを提供する。

## Tech Stack
- Language: Java
- Build Tool: Maven
- Frontend: React
- Fitbit API: Google Fitbit Web API
- AI: Claude API (Anthropic)
- DB: PostgreSQL
- Deploy: AWS

## Project Status
- [x] プロジェクト初期化
- [x] 企画策定 → docs/planning.md
- [x] 要件定義 → docs/requirements.md
- [x] 基本設計 → docs/basic-functional-design.md
- [x] アーキテクチャ設計 → docs/architecture.md
- [x] リポジトリ定義書 → docs/repository-structure.md
- [x] 開発ガイドライン → docs/development-guidelines.md
- [ ] 実装 ← 次のステップ
- [ ] テスト

## Directory Structure
```
docs/           - プロジェクトドキュメント
backend/        - バックエンド (Spring Boot)
frontend/       - フロントエンド (React)
docker/         - Docker関連 (ローカル開発用)
.github/        - CI/CD設定
.steering/      - 作業指針（タスク一覧・作業指示）
.questions/     - 技術Q&A記録
```

## Documents
セッション開始時やタスク実行時に、必要に応じて以下のドキュメントを参照すること。

| ドキュメント | ファイル | 用途 |
|-------------|---------|------|
| 企画書 | docs/planning.md | プロダクトコンセプト・技術スタック選定理由 |
| 要件定義書 | docs/requirements.md | 機能要件(FR-xxx)・非機能要件・KPI・制約事項 |
| 基本設計書 | docs/basic-functional-design.md | 機能一覧・画面一覧・データモデル・状態遷移・データフロー |
| アーキテクチャ設計書 | docs/architecture.md | レイヤー構成・パッケージ設計・インフラ・セキュリティ・外部API統合 |
| リポジトリ定義書 | docs/repository-structure.md | ディレクトリ構成・配置ルール・モジュール分割方針 |
| 開発ガイドライン | docs/development-guidelines.md | コーディング規約・命名規則・テスト方針・Git運用・レビュー基準 |
| チケット管理 | .steering/tasklist.md | 実装タスク一覧・進捗管理（PMが管理） |
| 作業指示 | .steering/TASK-xxx_{日付}.md | チケットをブレイクダウンした作業手順 |
| 技術Q&A | .questions/question-{日付}.md | ペアプロ中の技術的な質問と回答の記録 |

## Conventions
- ドキュメントは日本語で記述
- コミットメッセージは英語
- コードコメントは英語
- ユーザーから技術的な質問があった場合、回答後に `.questions/question-{YYYY-MM-DD}.md` に記録する
  - 同日のファイルが既にあれば追記する
  - 質問内容を見出し3（`###`）、回答内容をノーマルテキストで記載する
