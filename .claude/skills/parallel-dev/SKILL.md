---
name: parallel-dev
description: tmux と git worktree を使って複数のエージェントに並列でタスクを実行させるコマンドを生成するスキル。ユーザーが「並列で開発したい」「複数エージェントに振りたい」「並列実行したい」「tmuxで並列」「worktreeで並列」などと言った場合は必ずこのスキルを使うこと。タスクIDを指定された場合も、並列実行の文脈であればこのスキルを使う。
---

## 概要

このスキルは、`.steering/tasklist.md` の `parallel-group` フィールドを読み取り、複数のエージェントに並列でタスクを実行させるための tmux `send-keys` コマンドを生成する。

各エージェントは独立した git worktree 上で動作し、互いのコードベースに干渉しない。

---

## 手順

### Step 1: 並列候補タスクを選定する

`.steering/tasklist.md` を読み込み、以下の条件で並列候補を選ぶ:

1. **`parallel-group` が同じ**タスクを候補にする（例: `5-B` のタスクをまとめて提示）
2. `parallel-group` が異なっても、**ブロック関係のない未着手タスク**は並列候補になりうる
3. ステータスが `[ ]`（未着手）または確認が必要な `[>]`（進行中）のタスクのみ対象
4. **影響ファイル（`影響ファイル` フィールド）が重複しているタスクは並列不可**として除外する

選定したタスクを一覧で提示し、ユーザーに確認を取ること。

### Step 2: ペイン番号を確認する

ユーザーがペイン番号を指定していない場合は、以下のように確認する:

> 何番のペインを使いますか？（例: タスクAをペイン1、タスクBをペイン2）

ペイン番号が確定したら Step 3 に進む。

### Step 3: tmux コマンドを生成する

各タスクに対して以下のフォーマットで tmux `send-keys` コマンドを出力する:

```
ts {ペイン番号} "claude 'git worktree add ../{worktree-dir} {ブランチ名} && cd ../{worktree-dir} && {タスクID}: .steering/tasklist.md の受入条件に従い {実装内容の要約} を実装して。完了後に .steering/tasklist.md のステータスを [x] に更新して。'"
```

#### 命名規則

`{リポジトリ名}` は `basename $(git rev-parse --show-toplevel)` で取得する。

| 項目 | 形式 | 例（リポジトリ名が `fitbit-agent` の場合） |
|------|------|-----|
| worktree ディレクトリ | `../{リポジトリ名}-{タスクID小文字}` | `../fitbit-agent-task051` |
| ブランチ名 | `feature/{タスクID}-{説明}` | `feature/TASK-051-daily-advice` |

#### 実装内容の要約

- ワンライナーに収まる粒度で要約する
- 詳細は `docs/` と `.steering/tasklist.md` を参照させる
- **エージェントが自律的に完了まで実装する**前提で指示する

#### 出力例

リポジトリ名が `my-app`、タスクが TASK-010（認証機能）と TASK-011（ユーザー管理）の場合:

```bash
ts 1 "claude 'git worktree add ../my-app-task010 feature/TASK-010-auth && cd ../my-app-task010 && TASK-010: .steering/tasklist.md の受入条件に従い 認証機能（ログイン・トークン管理）を実装して。完了後に .steering/tasklist.md のステータスを [x] に更新して。'"

ts 2 "claude 'git worktree add ../my-app-task011 feature/TASK-011-user-management && cd ../my-app-task011 && TASK-011: .steering/tasklist.md の受入条件に従い ユーザー管理API（プロフィール取得・更新）を実装して。完了後に .steering/tasklist.md のステータスを [x] に更新して。'"
```

### Step 4: tasklist.md のステータスを更新する

コマンドを出力したら（ユーザーが実行する前でも）、着手するタスクのステータスを `[ ]` → `[>]` に更新する。

---

## 注意事項

- **`ts` は tmux send-keys のエイリアス**。ユーザーの環境に応じて `tmux send-keys -t {ペイン番号}` に読み替えてもよい
- **git worktree はリポジトリルートからの相対パス**で指定する（`backend/` 配下ではなくリポジトリルートの親ディレクトリ）
- **エージェントが worktree 内で作業するため、`.steering/tasklist.md` の更新はマージ競合が発生しやすい**。マージ後に手動確認を促すこと
- **各ペインのエージェントはツール使用の都度、ユーザーの許可を求める**。並列で複数ペインが動作している場合、許可リクエストが複数ペインから来ることに注意

---

## worktree のクリーンアップ

並列作業完了後、ユーザーがレビューを終えてマージした場合:

```bash
git worktree remove ../{リポジトリ名}-{タスクID小文字}
git branch -d feature/{タスクID}-{説明}
```

このコマンドもあわせて提示すること。`{リポジトリ名}` は worktree 作成時と同じ値を使う。
