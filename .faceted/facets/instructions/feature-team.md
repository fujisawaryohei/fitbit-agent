# Instruction: feature-team

Issue 番号またはタスクリストファイルから、バックエンド・フロントエンドのチームを自動起動する。
（旧 `.claude/skills/start-feature-team`）

## Step 0: 入力判定
`#7` 等 → Issue モード / ファイルパス → ファイルモード / 不明 → 確認する。

## Step 1A: Issue モード
`gh issue view {番号} --repo fujisawaryohei/fitbit-agent --json number,title,body`。
`aidlc-docs/` 等に既存タスクリストがないか確認し、あれば使うか新規分解か聞く。

## Step 1B: ファイルモード
指定ファイルを `Read`。チェックボックス形式 → そのまま採用 / JSON → `tasks` から取得 / 自由記述 → issue-planner で分解。

## Step 2: タスク分解（issue-planner）
バックエンド（FastAPI/Python）とフロントエンド（Next.js/TS）の実装タスクに分解させる（各々「何を」「参照ファイル」を含める）。

## Step 3: ユーザー確認
分解結果を見せて開始してよいか確認。

## Step 4: チーム・タスク作成
`TeamCreate(team_name="fitbit-feature", ...)`。backend / frontend / commit タスクを `TaskCreate`。
commit タスクは両タスクを `addBlockedBy`。片側のみなら該当タスクのみ。

## Step 5: エージェント起動（並列・background）
必要な側のみ起動: `fitbit-backend-dev`（name: backend-dev）/ `fitbit-frontend-dev`（name: frontend-dev）。
プロンプトに「完了後 team lead に報告」を含める。

## Step 6: 調整
完了報告を待ち、`TaskUpdate(status="completed")`。質問はユーザーに転送。

## Step 7: テスト・コミット
`uv run pytest backend/tests/ agent/tests/ --ignore=agent/tests/test_planning_tools_llm.py -q`、
`cd frontend && npx tsc --noEmit`、`git commit`、Issue モードなら `gh issue close`。
※ コミットは `policies/no-commit-without-permission` に従う。

## Step 8: 解散
起動したエージェントに `shutdown_request` → `TeamDelete()`。
