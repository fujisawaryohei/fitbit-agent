# Execution Plan — Fitbit Weight Management AI Agent

## 詳細分析サマリー

### 変更スコープ
- **変換タイプ**: Greenfield（完全新規構築）
- **主要変更**: フルスタックアプリ（Next.js + FastAPI + LangGraph）の新規開発
- **関連コンポーネント**: フロントエンド、バックエンドAPI、AIエージェント、Fitbit OAuth2、ベクトルストア

### 変更影響アセスメント
- **ユーザー影響**: あり — チャットUIを通じた直接インタラクション
- **構造変化**: あり — マルチサービス新規構築
- **データモデル**: あり — セマンティックメモリ（ベクトルストア）、Fitbitデータ構造
- **API**: あり — FastAPI新規設計、Fitbit OAuth2フロー
- **NFR影響**: あり — PBT有効（Hypothesis + fast-check）、メモリアーキテクチャ設計

### リスクアセスメント
- **リスクレベル**: Medium
- **ロールバック複雑度**: Easy（個人プロジェクト・ローカル実行）
- **テスト複雑度**: Moderate（PBT有効・複数コンポーネント連携）

---

## ワークフロービジュアライゼーション

```
INCEPTION PHASE
  [x] Workspace Detection    - COMPLETED
  [-] Reverse Engineering    - SKIPPED (Greenfield)
  [x] Requirements Analysis  - COMPLETED
  [x] User Stories           - COMPLETED
  [x] Workflow Planning      - IN PROGRESS
  [ ] Application Design     - EXECUTE
  [ ] Units Generation       - EXECUTE

CONSTRUCTION PHASE
  [ ] Functional Design      - EXECUTE
  [ ] NFR Requirements       - EXECUTE
  [ ] NFR Design             - EXECUTE
  [-] Infrastructure Design  - SKIPPED (ローカル実行・デプロイ後続)
  [-] Code Generation        - SKIPPED (ユーザー自己実装)
  [-] Build and Test         - SKIPPED (ユーザー自己実装)

OPERATIONS PHASE
  [-] Operations             - PLACEHOLDER
```

---

## 実行フェーズ詳細

### 🔵 INCEPTION PHASE

#### ✅ Workspace Detection — COMPLETED
- Greenfield プロジェクト確認

#### ⏭ Reverse Engineering — SKIPPED
- **理由**: 既存コードなし（Greenfield）

#### ✅ Requirements Analysis — COMPLETED
- 要件定義完了（FR-01〜06、NFR-01〜04）

#### ✅ User Stories — COMPLETED
- 5 Epic、15 User Story、8 LangGraph Tools 定義

#### ✅ Workflow Planning — IN PROGRESS（このドキュメント）

#### ▶️ Application Design — EXECUTE
- **理由**: 新規コンポーネント多数（FastAPI、LangGraph Agent、Next.js UI、Fitbit OAuth2、Vector Store）
- **成果物**: コンポーネント図、サービス定義、インターフェース設計

#### ▶️ Units Generation — EXECUTE
- **理由**: フロントエンド・バックエンド・AIエージェントの3サービス構成、並列開発の分割が必要
- **成果物**: unit-of-work.md、unit-of-work-dependency.md、unit-of-work-story-map.md

---

### 🟢 CONSTRUCTION PHASE

#### ▶️ Functional Design — EXECUTE（Units毎）
- **理由**: カロリー計算ロジック・セマンティックメモリ管理・LangGraph ツールルーティングなど複雑なビジネスロジック
- **PBT-01 適用**: 各ユニットで testable properties を特定・文書化

#### ▶️ NFR Requirements — EXECUTE（Units毎）
- **理由**: PBT有効（Hypothesis + fast-check）、メモリアーキテクチャ（in-context + semantic）の選定が必要
- **PBT-09 適用**: フレームワーク選定をここで確定

#### ▶️ NFR Design — EXECUTE（Units毎）
- **理由**: NFR Requirements 実行のため必須。PBTパターン・セマンティックメモリのベクトルストア設計を行う

#### ⏭ Infrastructure Design — SKIPPED
- **理由**: 初期フェーズはローカル実行のみ。クラウドデプロイは設計完了後に別途検討

#### ⏭ Code Generation — SKIPPED
- **理由**: ユーザーが自己実装予定。設計成果物（Functional Design、NFR Design）を実装ガイドとして活用

#### ⏭ Build and Test — SKIPPED
- **理由**: ユーザーが自己実装・テスト実施予定

---

## 成功基準

- [ ] Application Design 完了（コンポーネント・サービス・インターフェース定義）
- [ ] Units Generation 完了（作業単位の分割・依存関係・ストーリーマッピング）
- [ ] Functional Design 完了（全ユニットのビジネスロジック・PBT-01 プロパティ特定）
- [ ] NFR Requirements 完了（PBTフレームワーク選定・非機能要件確定）
- [ ] NFR Design 完了（PBTパターン・メモリアーキテクチャ設計）
- [ ] ユーザーが設計成果物をもとに実装を開始できる状態になること

---

## 想定タイムライン（AI-DLC フェーズ）

| フェーズ | ステージ | ステータス |
|---------|---------|-----------|
| INCEPTION | Application Design | 次のステップ |
| INCEPTION | Units Generation | Application Design 後 |
| CONSTRUCTION | Functional Design（各Unit） | Units Generation 後 |
| CONSTRUCTION | NFR Requirements（各Unit） | Functional Design 後 |
| CONSTRUCTION | NFR Design（各Unit） | NFR Requirements 後 |
