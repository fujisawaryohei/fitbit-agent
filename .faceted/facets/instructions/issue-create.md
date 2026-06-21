# Instruction: issue-create

やりたいことから GitHub Issue を作成し Project に追加する。
（旧 `.claude/skills/github-issue-create`）

## Step 0: 事前確認
`gh auth status` / `gh project list --owner <owner>` を確認。
認証不可 → `gh auth login` を案内して終了。project スコープ無し → Classic PAT 再認証を案内。
Project が 1 つだけなら自動選択してよいか確認。

## Step 1: ヒアリング
「何をやりたいですか？背景・問題点も含めて教えてください。」だけを聞く（この時点で深掘りしない）。

## Step 2: 仕様策定（issue-planner ペルソナ）
回答を渡し、種別 / タイトル / 概要 / 仕様 / TODO / 参照ドキュメント / 完了条件を出力させる。
確認質問が出たらユーザーに転送して回答を渡す。

## Step 3: ユーザー確認
出力を見せ「この内容で登録してよいですか？」。修正があれば反映して再確認。承認を得たら次へ。

## Step 4: Issue 作成
```bash
gh issue create --title "{種別}: {タイトル}" --body "## 概要 ... ## 仕様 ... ## TODO ... ## 参照ドキュメント ... ## 完了条件 ..."
```

## Step 5: Project 追加
```bash
gh project item-add {project番号} --owner {owner} --url {issue_url}
```

## Step 6: 完了報告
タイトル・URL・追加先 Project を報告し、続けて別 Issue を登録するか確認する。

→ 出力形式: `output-contracts/issue.md`
