# TAKT の rules とルーティングの仕組み

TAKT（[nrslib/takt](https://github.com/nrslib/takt)）のワークフローにおける `rules` の役割と、
ステップ間ルーティングがどう決定されるかを、ソースコードを読んで整理したもの。

調査対象ワークフロー: `.takt/workflows/multi-provider-review.yaml`
（Claude が実装プランを作成 → Codex がレビュー、最大3ループ）

---

## 1. 結論サマリ

- `rules` は **「ルーティング先の定義」** と **「判定プロンプトの生成元」** の二役を担う。
- ステップの実行は **3フェーズ**に分かれ、ルーティング判定は作業（Phase 1）とは独立した **Phase 3** で行われる。
- 通常文字列の `condition` は **conductor という判定専用AIエージェント**が多肢選択で分類する。
- `ai("...")` の `condition` は **ペルソナなしの汎用ジャッジAI**が個別条件として評価する。
- `COMPLETE` / `ABORT` / `when:` などの確定値は **AIを呼ばず決定論的**に分岐する。

---

## 2. condition は「予約語」ではなく「output contract」

`condition` の文字列は自由に書けるが、内部では予約語ではない。
ステップ実行時、TAKT が `rules` から **判定用の選択肢テーブル**を自動生成し、AIに提示する。

`src/core/workflow/instruction/status-rules.ts` の `generateStatusRulesComponents()` が
`rules` をループして以下を生成する（タグの接頭辞は `stepName.toUpperCase()`）。

```
| # | 状況 | タグ |
|---|------|------|
| 1 | Approved | `[REVIEW:1]` |        ← rules[0].condition
| 2 | Needs revision | `[REVIEW:2]` |   ← rules[1].condition
```

- `condition` の文字列 = AIに見せる**選択肢ラベル（output contract）**
- AIは対応する `[<STEPNAME>:N]` タグを出力
- TAKT はタグの **N（インデックス）** で `rules[N-1].next` へ遷移

> ドキュメント上の `[STEP:N]` は一般化表記。実際は `[PLAN:1]` `[REVIEW:2]` のようにステップ名の大文字になる。

---

## 3. ステップ実行の3フェーズモデル

`src/core/workflow/engine/StepExecutor.ts` より。

| Phase | 役割 | ツール | instruction | rules を見るか |
|---|---|---|---|---|
| **Phase 1** | 本来の作業（plannerがプラン作成など） | あり | `step.instruction` を使用 | **見ない** |
| Phase 2 | レポート出力（任意） | Write のみ | — | — |
| **Phase 3** | **状態判定 ＝ ルーティング** | なし | `rules` から自動生成 | 見る |

### 重要な含意

- **ルーティングは Phase 1 の instruction に依存しない。** Phase 3 が独立して判定する。
- Phase 1 のプロンプトテンプレート（`src/shared/prompts/*/perform_phase1_message.md`）には
  `condition` も判定タグも**含まれない**。作業者は条件の存在を知らない。
- したがって **「instruction と judge プロンプトの整合を取る」という問題は発生しない**。
  両プロンプトは依存関係を持たず、判定者が Phase 1 の生の出力を読んで解釈するだけ。

### なぜ整合不要で成立するか

```
Phase 1: planner がプランを書く（conditionは知らない）
              │ 出力（プラン本文）
              ▼
Phase 3: 判定者がプラン本文を読む
         「この内容は Planning complete か？ Cannot proceed か？」
         ＝ rules を選択肢に、出力内容から判定
              │
              ▼
         [PLAN:1] を出力 → next: review
```

これは TAKT の設計哲学 **"Separation Improves Quality"** に対応する。
実装ステップは自分自身をレビュー（＝ルーティング判定）せず、判定者が唯一の真実源になる。

instruction に「Approvedを選択してください」と書くのは必須ではなく、
作業者が結論を明示しやすくして**判定精度を上げる補助**にすぎない。

---

## 4. 判定者の実態：AIエージェント + 決定論的制御のハイブリッド

`src/agents/structured-caller/prompt-based-structured-caller.ts` の `judgeStatus()` より。

判定の**頭脳はLLM呼び出し**だが、入出力の制御・検証・フォールバックは決定論的コードで包まれている。

```
judgeStatus()
│
├─ rules が1個だけ → auto_select（AI呼ばずに即決）          ★決定論
│
├─ Stage 1: conductor AI を structured output で呼ぶ        ★AI
│     └─ JSON を parseLastJsonBlock で抽出・範囲検証        ★決定論
│
├─ Stage 2: 失敗時 → tag judge（AIに [STEP:N] を出させる）  ★AI
│     └─ detectJudgeIndex でタグ抽出                         ★決定論
│
└─ Stage 3: さらに失敗 → evaluateCondition フォールバック    ★AI
```

判定専用に**プロバイダーAPIを追加で1回（以上）呼ぶ**ため、各ステップでコストとレイテンシが上乗せされる点に注意。

---

## 5. conductor と `ai()` の違い

どちらもAI判定だが、担当者・評価方式・タイミングが異なる。

| 観点 | 通常文字列 condition（conductor） | `ai("...")` condition |
|---|---|---|
| AIの呼び方 | `runAgent('conductor', ...)` | `runAgent(undefined, ...)` |
| Persona | **conductor**（判定専用ペルソナ） | **なし**（汎用ジャッジ） |
| 実行場所 | 独立した **Phase 3** | RuleEvaluator の評価順の中 |
| 評価方式 | **多肢選択分類**（全ルールを選択肢に1つ選ぶ） | **条件マッチ**（`ai()`付きルールを個別に該当判定） |
| プロンプト | criteriaTable（番号付き選択肢表＋タグ） | `buildJudgePrompt`（条件リスト） |
| maxTurns | 3 | 1 |
| 構造化出力 | あり（失敗時タグfallback） | なし（テキスト解析） |

### 概念の違い

- **conductor（通常文字列）**: 「この出力は次の選択肢のうちどれに最も該当するか？」
  → 全ルールを**相互排他の選択肢**として提示し、専門ペルソナが分類。
- **`ai()`**: 「この出力は、この条件を満たすか？」
  → 指定条件を**個別**に汎用ジャッジが該当判定。

---

## 6. ルール評価の優先順位

`src/core/workflow/evaluation/RuleEvaluator.ts` の評価順（first match wins）。
通常文字列・`ai()`・確定値は同一ステップに混在でき、以下の順で評価される。

```
1.  aggregate (all()/any()) — 並列ステップの集約
2.  先行する確定的 when 条件（Phase 3 タグより前）
3.  Phase 3 出力のタグ検出           ← 通常文字列（conductor）はここ
4.  先行する確定的 when 条件（Phase 1 タグより前）
5.  Phase 1 出力のタグ検出（fallback）
6.  先行する確定的 when 条件（ai() ルールより前）
7.  ai() 条件の評価（AIジャッジ）     ← ai() はここ
8.  残りの確定的 when 条件
9.  全条件 AI judge（最終フォールバック）
10. 遅延確定フォールバック（when: true など）
```

→ **通常文字列（conductor）の方が `ai()` より先に評価される。**

---

## 7. 使い分け指針

| 場面 | 推奨 |
|---|---|
| 作業出力を「状態」として分類したい（完了/失敗/要修正） | 通常文字列（conductor）。専門ペルソナで判定精度が高い |
| 「特定条件が成立しているか」を明示的に問いたい | `ai("...")`。条件文を完全にコントロールできる |
| 確定的に分岐したい（コスト・レイテンシ削減） | `COMPLETE` / `ABORT` / `when:` など決定論的 condition |

---

## 8. 責務の分離まとめ

| 要素 | 決めること | 出どころ |
|---|---|---|
| **Persona** | WHO（作業者の役割・思考スタイル・行動規範） | `personas/*.md`（条件は定義しない） |
| **Instruction** | HOW（Phase 1 で何をするか） | ワークフローの `instruction`（ルーティングには無関係） |
| **rules の condition** | WHAT（次にどう分岐するか＝判定の選択肢） | ワークフローの `rules` |

同じ Persona でも、ワークフロー側の `rules` 次第で output contract（分岐の選択肢）は変わる。
→ Persona は「振る舞い」だけを担い、分岐は完全に `rules` でコントロールするため、Persona を使い回せる。

---

## 参照したソース

| ファイル | 内容 |
|---|---|
| `src/core/workflow/engine/StepExecutor.ts` | 3フェーズモデルの定義 |
| `src/core/workflow/instruction/InstructionBuilder.ts` | Phase 1 プロンプト構築 |
| `src/core/workflow/instruction/StatusJudgmentBuilder.ts` | Phase 3 判定プロンプト構築 |
| `src/core/workflow/instruction/status-rules.ts` | rules → 選択肢テーブル生成 |
| `src/shared/prompts/*/perform_phase1_message.md` | Phase 1 テンプレート（条件を含まない） |
| `src/core/workflow/phase-runner.ts` | `needsStatusJudgmentPhase` / `hasTagBasedRules` |
| `src/core/workflow/evaluation/RuleEvaluator.ts` | ルール評価順・`ai()`評価 |
| `src/agents/structured-caller/prompt-based-structured-caller.ts` | `judgeStatus` / `evaluateCondition` の実装 |
| `builtins/{en,ja}/facets/personas/planner.md` | Persona の実例（条件を含まない） |
