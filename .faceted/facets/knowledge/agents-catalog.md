# Knowledge: agents-catalog

利用可能なペルソナ（旧 `~/.claude/agents/` + プロジェクト agents）と起動タイミング。
各ペルソナの詳細は `facets/persona/*.md` を参照。

| persona | 目的 | 使うとき |
|---|---|---|
| planner | 実装計画 | 複雑な機能・リファクタ |
| architect | システム設計 | アーキテクチャ判断 |
| tdd-guide | テスト駆動開発 | 新機能・バグ修正 |
| code-reviewer | コードレビュー | コードを書いた直後 |
| security-reviewer | セキュリティ分析 | コミット前・入力/認証/API を扱う後 |
| database-reviewer | DB レビュー | SQL・マイグレーション・スキーマ |
| build-fixer | ビルドエラー解消 | ビルド失敗時 |
| e2e-runner | E2E テスト | 重要なユーザーフロー |
| refactor-cleaner | デッドコード掃除 | コード保守 |
| doc-updater | ドキュメント更新 | codemap / docs |
| docs-lookup | ライブラリ/API 調査 | 使い方・最新例が必要なとき |
| loop-operator | 自律ループ運用 | ループ監視・介入 |
| backend-dev | fitbit バックエンド実装 | FastAPI/Python タスク |
| frontend-dev | fitbit フロントエンド実装 | Next.js/TS タスク |
| issue-planner | Issue 仕様策定 | Issue 起票・タスク分解 |

## 即時起動（ユーザー指示不要）
- 複雑な機能 → planner
- コードを書いた/変更した直後 → code-reviewer
- バグ修正/新機能 → tdd-guide
- アーキテクチャ判断 → architect

## 並列実行
独立した作業は並列で起動する（例: セキュリティ分析・性能レビュー・型チェックを同時）。

## 分割ロール分析
複雑な問題には複数視点のサブエージェントを使う:
事実確認・シニアエンジニア・セキュリティ・一貫性・冗長性チェック。
