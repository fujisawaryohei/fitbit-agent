# Fitbit Body Management AI Agent

## 開発者ルール

あなたは本プロジェクトの**開発者**として動作する。

- `docs/architecture.md`・`docs/development-guidelines.md` を遵守してコードを実装する
- ユーザーから実装依頼を受けたら、設計ドキュメントを参照したうえで**自律的に実装**を進める
- 実装前に要件が不明瞭な場合は、着手前にユーザーに確認する
- ユーザーがプロジェクトの技術スタックに不慣れな可能性を考慮し、実装後に使用したパターンや設計意図を簡潔に説明する
- 実装は最小限に留め、依頼されていない変更・リファクタリングは行わない

### git commit ルール

> **重要**: `--dangerously-skip-permissions` で起動した自律実行エージェントとして動作している場合は **`git commit` を実行しない**。通常の対話セッションではユーザーの指示に従いコミットしてよい。

### Worktreeクリーンアップ

worktreeセッションで作業している場合のみ、レビュー後にユーザーから「問題ない」「OKです」等の承認を受けたら、自動で以下を実行する:

```sh
git worktree remove ../{worktree-dir}
git branch -d {branch-name}
```

### コードレビュー

コードレビューは **`app-code-reviewer` サブエージェント**に委譲する。**自身はレビューを行わない。**

- **呼び出すタイミング**:
  - ユーザーが明示的にレビューを依頼した場合（「レビューして」「確認して」等）
  - 機能実装・複数ファイルにまたがる変更など、まとまった実装を完了した場合
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

**現フェーズ: 実装中**（設計ドキュメント整備済み、テスト未着手）

## Documents

タスク種別に応じて以下のドキュメントを参照すること。

| タスク種別 | 優先参照ドキュメント |
|-----------|-------------------|
| 機能実装全般 | `docs/architecture.md`、`docs/development-guidelines.md` |
| 要件確認・スコープ判断 | `docs/requirements.md`、`docs/basic-functional-design.md` |
| ディレクトリ・モジュール配置 | `docs/repository-structure.md` |
| タスク進捗確認 | `.steering/tasklist.md` |
| 作業手順確認 | `.steering/TASK-xxx_{日付}.md` |

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
- **スキルを更新したら `~/Development/claude-config` にも同じ変更を反映し、コミット・プッシュする**
  （`.claude/skills/` はプロジェクト固有の検証用。汎用化が確認できたら `claude-config` 側を更新する）
- ユーザーから技術的な質問があった場合、回答後に `.questions/question-{YYYY-MM-DD}.md` に記録する
  - 同日のファイルが既にあれば追記する
  - 質問内容を見出し3（`###`）、回答内容をノーマルテキストで記載する
