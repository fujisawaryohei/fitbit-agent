# GitHub Workflow Knowledge

Issue / PR の運用と `gh` CLI の使い方。Issue 取得・記録・PR 作成のステップで参照する。

## 前提

- `gh` CLI が認証済みであること（`gh auth status` で確認可能）
- TAKT は隔離 worktree 上の専用ブランチで実行される。実装の差分はこのブランチに乗る

## チケット番号の受け取り

- チケット番号はタスク入力（`{task}`）に含まれる（例: `#42`、`42`、`Issue 42`）
- 入力から数字を抽出して Issue 番号として扱う

## よく使うコマンド

| 目的 | コマンド例 |
|------|-----------|
| Issue 取得 | `gh issue view <番号> --json title,body,comments` |
| Issue にコメント | `gh issue comment <番号> --body-file <file>` |
| 現在の差分確認 | `git status` / `git diff` |
| ブランチ確認 | `git branch --show-current` |
| コミット | `git add -A && git commit -m "<type>: <summary>"` |
| push | `git push -u origin <branch>` |
| PR 作成 | `gh pr create --title "<title>" --body-file <file>` |

## 注意

- 破壊的・外向きのコマンドは対象を確認してから実行する
- 本文は一時ファイルに書いて `--body-file` で渡すと、特殊文字の事故を避けられる
