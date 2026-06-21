# .facted — Faceted Prompting で整理した Claude 設定

`~/.claude`（グローバル rules / agents）とプロジェクトの `.claude`・`CLAUDE.md` に
散らばっていた指示を、**関心ごと（facet）に分割**して再編成したもの。

> 長いプロンプトが問題なのは「長いこと」ではなく「関心が混ざること」。
> 役割・ルール・知識・手順・出力仕様が 1 ファイルに混在すると、どこを直せばいいか分からなくなる。
> facet ごとに部品化し、composition で組み合わせる。

参考: [Faceted Prompting の基本構造と実装方法](https://zenn.dev/nrs/articles/88f158aca0505b)

## 5 つの facet

| facet | 問い | 置き場所 | 例 |
|---|---|---|---|
| **persona** | どう振る舞うか | `personas/` | backend-dev, reviewer, planner |
| **policy** | 何を守るか | `policies/` | immutability, testing, security |
| **knowledge** | 何を知っているか | `knowledge/` | project-backend, design-patterns |
| **instruction** | 何をするか | `instructions/` | feature-development, create-pr |
| **output-contract** | どんな形式で返すか | `output-contracts/` | issue, pull-request, plan |

## composition 層

`compositions/*.yaml` が facet を組み合わせて 1 つの設定にする。
部品を 1 箇所直せば、それを参照する全 composition に反映される。

```yaml
# 例: compositions/coding-backend.yaml
persona: backend-dev
policies: [immutability, error-handling, testing, code-quality]
knowledge: [project-backend, design-patterns]
instructions: [feature-development, research-and-reuse]
output_contracts: [pull-request]
```

## ディレクトリ構成

```
.facted/
├── compositions/      # facet を束ねた設定（用途単位）
├── personas/          # 役割・振る舞い
├── policies/          # 守るべきルール
├── knowledge/         # 背景知識・コンテキスト
├── instructions/      # 具体的な作業手順
└── output-contracts/  # 出力フォーマット仕様
```

## 既存資産との対応

- `~/.claude/rules/*` → `policies/` + `knowledge/`
- `~/.claude/agents/*`, `.claude/agents/*` → `personas/`（振る舞いのみ抽出）
- `.claude/skills/*` → `instructions/`
- `CLAUDE.md`（AIDLC ワークフロー）→ `knowledge/aidlc-workflow.md`
- 既存の `.takt/facets/*` と同じ facet モデル（こちらは Claude 設定全体を対象に拡張）

## 使い方

composition を選び、参照されている facet を順に読み込んで system / user プロンプトを構成する。
Claude Code のスキルや Codex の設定として流用することも想定。
