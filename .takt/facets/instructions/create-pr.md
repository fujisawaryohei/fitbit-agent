承認された実装をコミットし、Pull Request を作成してください。

**手順:**
1. `git status` / `git diff` で変更内容を確認する
2. `git add -A` でステージし、Conventional Commits 形式でコミットする
   - 例: `feat: <要約>` / `fix: <要約>`（AI 署名・Co-Authored-By は付けない）
3. `git push -u origin <現在のブランチ>` で push する
4. PR 本文を一時ファイル（例: `/tmp/pr-body.md`）に書き出す
   - 概要・変更点・対応する Issue（`Closes #<番号>`）・テスト結果を含める
5. `gh pr create --title "<title>" --body-file /tmp/pr-body.md` で PR を作成する
6. 作成された PR の URL を報告する

**注意:**
- 1 タスク = 1 PR。無関係な変更を含めない
- 各コマンドの結果を確認する。失敗した場合は理由を報告し `Cannot proceed` を選択する

PR の作成に成功したら `PR created` を選択してください。
