# Knowledge: aidlc-workflow

プロジェクトの `CLAUDE.md` に定義された Adaptive Software Development Lifecycle (AIDLC) ワークフローの要約。
ソフトウェア開発要求時は他の組み込みワークフローより優先される。

## 原則
**ワークフローが作業に適応する**（逆ではない）。モデルが以下から必要な段階を判断する:
1. ユーザーの意図と明確さ 2. 既存コードベースの状態 3. 変更の複雑さ・範囲 4. リスク・影響

## フェーズと段階

### INCEPTION（何を・なぜ作るか）
- Workspace Detection（必須）
- Reverse Engineering（ブラウンフィールドのみ）
- Requirements Analysis（必須・深度可変: minimal/standard/comprehensive）
- User Stories（条件付き）
- Workflow Planning（必須）
- Application Design（条件付き）
- Units Generation（条件付き）

### CONSTRUCTION（どう作るか）
ユニットごとのループ: Functional Design → NFR Requirements → NFR Design → Infrastructure Design →
Code Generation（必須）。全ユニット完了後に Build and Test（必須）。

### OPERATIONS
プレースホルダ（将来のデプロイ・監視）。

## 重要な規約
- 各段階で**明示的な承認**を待つ（DO NOT PROCEED until user confirms）。
- Construction の各段階は標準化された 2 択完了メッセージを使う（3 択等の創発的挙動は禁止）。
- 全ユーザー入力を `aidlc-docs/audit.md` に**生のまま追記**で記録（要約・上書き禁止）。
- アプリコードはワークスペース直下、ドキュメントは `aidlc-docs/` のみ。
- ルール詳細は `.aidlc-rule-details/` 等の解決済みディレクトリから都度ロードする。

> 注: 完全な定義は実体である `CLAUDE.md` を参照。本ファイルは facet 化のための要約。
