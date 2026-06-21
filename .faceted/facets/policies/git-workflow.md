# Policy: git-workflow

## コミットメッセージ形式
```
<type>: <description>

<optional body>
```
type: feat, fix, refactor, docs, test, chore, perf, ci

帰属（Co-Authored-By 等）はグローバル設定で無効化済み。

## Pull Request
1. 最新コミットだけでなく全コミット履歴を分析する。
2. `git diff <base-branch>...HEAD` で全変更を見る。
3. 網羅的な PR サマリを書く。
4. テストプランを TODO 付きで含める。
5. 新規ブランチは `-u` で push する。
