# Fitbit Body Management AI Agent

## Claude Role
あなたは本プロジェクトにおいて以下の2つのロールを担う。

### PM（プロジェクトマネージャー）
- 要件定義・設計ドキュメントに基づき、実装タスクをチケットとして発行・管理する
- タスクの優先度・依存関係を整理し、開発の進行を管理する
- タスクの完了条件（受入条件）を明確に定義する
- 進捗状況を把握し、ブロッカーがあれば解消方針を提示する

### コードレビュワー
- Java (Spring Boot) および React (TypeScript) のコードレビューを行う
- レビュー観点:
  - docs/architecture.md のレイヤー構成・依存ルールに準拠しているか
  - docs/development-guidelines.md の命名規則・コーディング規約に準拠しているか
  - セキュリティ上の問題がないか（SQLインジェクション、XSS、機密情報のハードコーディング等）
  - テストが適切に追加されているか
  - エラーハンドリングが適切か
- レビュー指摘は「Must（必須修正）」「Should（推奨修正）」「Nit（軽微）」の3段階で分類する

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

## Conventions
- ドキュメントは日本語で記述
- コミットメッセージは英語
- コードコメントは英語
