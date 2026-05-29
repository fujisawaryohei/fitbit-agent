---
name: start-feature-team
description: GitHub Issue 番号またはローカルのタスクリストファイルを渡すだけでバックエンド・フロントエンドのエージェントチームを自動起動する。「Issue #X を実装して」「#X チームで着手して」「start-feature-team #X」「このファイルでチームを起動して」などの指示で起動。
---

# フィーチャーチーム自動起動スキル

Issue 番号またはタスクリストファイルを受け取り、タスク分解 → チーム作成 → 並列実装 → コミット・クローズまでを自動化する。

---

## Step 0: 入力の判定

ユーザーのメッセージから入力種別を判定する:

| 入力パターン | 判定 |
|---|---|
| `#7`、`Issue 7`、`7番` など | → **Issue モード** |
| ファイルパス（`.md`、`.txt`、`.json` 等）| → **ファイルモード** |
| どちらか不明 | → 「Issue 番号かファイルパスを教えてください」と聞く |

---

## Step 1A: Issue モード — Issue 内容の取得

```bash
gh issue view {番号} --repo fujisawaryohei/fitbit-agent --json number,title,body
```

### タスクリストの存在確認

Issue 取得後、以下のパスに既存のタスクリストファイルがないか確認する:

```bash
# aidlc-docs 配下の該当 Issue に関連するファイルを探す
find /home/ubuntu/Project/fitbit-agent/aidlc-docs -name "*.md" | xargs grep -l "#{番号}\|{title}" 2>/dev/null

# qa-docs や他の場所も確認
find /home/ubuntu/Project/fitbit-agent -maxdepth 3 \
  -name "*task*" -o -name "*todo*" -o -name "*plan*" 2>/dev/null | grep -v node_modules | grep -v .git
```

- **既存ファイルが見つかった場合**: 内容を表示し「このタスクリストを使いますか？それとも Issue から新たに分解しますか？」と確認する
- **見つからない場合**: Step 2 へ進む

---

## Step 1B: ファイルモード — タスクリストファイルの読み込み

指定されたファイルを `Read` で読み込む。

ファイル形式に応じて解釈:
- **Markdown チェックボックス形式** (`- [ ] ...`): そのままタスクとして使用
- **JSON 形式**: `tasks` キーからタスク一覧を取得
- **自由記述**: `issue-planner` エージェントに渡してバックエンド/フロントエンドに分解させる

Issue 番号が含まれている場合は `gh issue view` で補足情報を取得する（任意）。

---

## Step 2: タスク分解（issue-planner エージェント）

既存タスクリストがない場合、または自由記述ファイルの場合に実行する。

`issue-planner` エージェントに以下を渡してバックエンド・フロントエンドのタスクに分解させる:

> 「以下の内容をバックエンド（FastAPI/Python）とフロントエンド（Next.js/TypeScript）の実装タスクに分解してください。
> それぞれに『何をすべきか』『参照すべきファイル』を含めてください。
>
> {Issue または ファイル内容}」

---

## Step 3: ユーザー確認

分解・読み込み結果をユーザーに見せて確認を取る:

> 「以下のタスクで実装を開始してよいですか？
>
> **バックエンド**: {内容}
> **フロントエンド**: {内容}」

「はい」の場合は Step 4 へ進む。修正依頼があれば対応してから再確認する。

---

## Step 4: チームとタスクの作成

### チーム作成
```
TeamCreate(team_name="fitbit-feature", description="Issue #{番号} or {ファイル名}: {タイトル}")
```

### タスク作成
分解結果をもとに TaskCreate でタスクを登録する:
- バックエンドタスク（backend-dev 担当）
- フロントエンドタスク（frontend-dev 担当）
- コミットタスク（両タスク完了後、team-lead 担当）

コミットタスクには `addBlockedBy` でバックエンド・フロントエンドの両タスクを設定する。
バックエンドのみ / フロントエンドのみの場合は該当タスクのみ作成する。

---

## Step 5: エージェント起動

タスク内容に応じて必要なエージェントのみ **並列で** 起動する（`run_in_background: true`）:

### backend-dev（バックエンドタスクがある場合）
- `subagent_type`: `fitbit-backend-dev`
- `team_name`: `fitbit-feature`
- `name`: `backend-dev`
- プロンプト: バックエンドタスクの詳細 + 「完了後に team lead に報告してください」

### frontend-dev（フロントエンドタスクがある場合）
- `subagent_type`: `fitbit-frontend-dev`
- `team_name`: `fitbit-feature`
- `name`: `frontend-dev`
- プロンプト: フロントエンドタスクの詳細 + 「完了後に team lead に報告してください」

---

## Step 6: 完了待ちと調整

- 両エージェントの完了報告を待つ
- 完了したタスクは `TaskUpdate(status="completed")` で更新する
- エージェントから質問が来た場合はユーザーに転送して回答を得る

---

## Step 7: テスト確認とコミット

両タスク完了後:

1. テスト実行（バックエンドがある場合）:
   ```bash
   uv run pytest backend/tests/ agent/tests/ --ignore=agent/tests/test_planning_tools_llm.py -q
   ```

2. 型チェック（フロントエンドがある場合）:
   ```bash
   cd /home/ubuntu/Project/fitbit-agent/frontend && npx tsc --noEmit
   ```

3. コミット:
   ```bash
   git add -A
   git commit -m "feat: {タイトルを要約したメッセージ}"
   ```

4. Issue クローズ（Issue モードの場合のみ）:
   ```bash
   gh issue close {番号} --repo fujisawaryohei/fitbit-agent --comment "実装完了。commit: {hash}"
   ```

---

## Step 8: チーム解散

```
SendMessage(to="backend-dev", {"type": "shutdown_request"})   # 起動した場合のみ
SendMessage(to="frontend-dev", {"type": "shutdown_request"})  # 起動した場合のみ
```
シャットダウン確認後:
```
TeamDelete()
```
