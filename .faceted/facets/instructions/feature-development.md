# Instruction: feature-development

機能実装のパイプライン（リサーチ → 計画 → TDD → レビュー → git）。

0. **Research & Reuse**（新規実装前に必須）→ `instructions/research-and-reuse.md`
1. **Plan First**: planner で実装計画を作る。依存・リスクを洗い、フェーズに分解する。
2. **TDD**: tdd-guide。テストを先に書き（RED）→ 実装（GREEN）→ リファクタ（IMPROVE）→ カバレッジ 80%+。
3. **Code Review**: コードを書いた直後に code-reviewer。CRITICAL・HIGH を是正、MEDIUM は可能な限り対応。
4. **Commit & Push**: Conventional Commits 形式。**ユーザーの明示的指示があるまでコミットしない**（→ `policies/no-commit-without-permission`）。

## プロジェクト内の実装手順（fitbit-agent）
1. 既存ファイルを必ず `Read` してからコードを書く。
2. 既存パターン（命名・スタイル・エラーハンドリング）に揃える。
3. 実装後に検証する:
   - バックエンド: `uv run pytest backend/tests/ -q`
   - フロントエンド: `cd frontend && npx tsc --noEmit`
4. 完了後、team lead に報告する。
