# リポジトリ定義書: Fitbit Body Management AI Agent

## 目次
1. [はじめに](#1-はじめに)
2. [プロジェクト全体構成](#2-プロジェクト全体構成)
3. [バックエンド ディレクトリ構成](#3-バックエンド-ディレクトリ構成)
4. [フロントエンド ディレクトリ構成](#4-フロントエンド-ディレクトリ構成)
5. [設定ファイル一覧](#5-設定ファイル一覧)
6. [モジュール分割方針](#6-モジュール分割方針)

---

## 1. はじめに

### 1.1 本ドキュメントの目的
本ドキュメントは、リポジトリのディレクトリ構成と各ディレクトリの役割を定義する。
新規ファイルの配置先を迷わないための指針として利用する。

### 1.2 関連ドキュメント
| ドキュメント | ファイル |
|-------------|---------|
| アーキテクチャ設計書 | docs/architecture.md |
| 開発ガイドライン | docs/development-guidelines.md |

---

## 2. プロジェクト全体構成

```
fitbit-agent/
├── docs/                              # プロジェクトドキュメント
│   ├── planning.md                    #   企画書
│   ├── requirements.md                #   要件定義書
│   ├── basic-functional-design.md     #   基本設計書
│   ├── architecture.md                #   アーキテクチャ設計書
│   ├── repository-structure.md        #   リポジトリ定義書（本ドキュメント）
│   └── development-guidelines.md      #   開発ガイドライン
├── backend/                           # バックエンド (Spring Boot)
│   ├── src/
│   ├── pom.xml
│   └── Dockerfile
├── frontend/                          # フロントエンド (React)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker/                            # Docker関連
│   └── docker-compose.yml             #   ローカル開発用
├── .github/                           # GitHub設定
│   └── workflows/
│       └── ci.yml                     #   CI/CDパイプライン
├── CLAUDE.md                          # Claude Code 設定
├── .gitignore
└── README.md
```

**配置ルール**:
- `docs/` にはプロジェクト管理ドキュメントのみ配置する（API仕様書等の自動生成物は除く）
- `backend/` と `frontend/` は完全に独立したモジュールとして管理する
- ルートディレクトリにはプロジェクト全体に関わるファイルのみ配置する

---

## 3. バックエンド ディレクトリ構成

```
backend/
├── src/
│   ├── main/
│   │   ├── java/com/fitbitagent/
│   │   │   ├── FitbitAgentApplication.java
│   │   │   ├── controller/
│   │   │   ├── service/
│   │   │   ├── repository/
│   │   │   ├── domain/
│   │   │   │   ├── entity/
│   │   │   │   └── enums/
│   │   │   ├── client/
│   │   │   │   ├── fitbit/
│   │   │   │   │   ├── dto/
│   │   │   │   │   ├── FitbitApiClient.java
│   │   │   │   │   ├── FitbitOAuthClient.java
│   │   │   │   │   └── FitbitRateLimiter.java
│   │   │   │   └── claude/
│   │   │   │       ├── dto/
│   │   │   │       ├── ClaudeApiClient.java
│   │   │   │       └── PromptBuilder.java
│   │   │   ├── dto/
│   │   │   │   ├── request/
│   │   │   │   └── response/
│   │   │   ├── config/
│   │   │   └── exception/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       ├── prompts/
│   │       │   ├── daily-advice.txt
│   │       │   ├── weekly-report.txt
│   │       │   └── chat-system.txt
│   │       └── db/migration/
│   │           ├── V1__create_users.sql
│   │           ├── V2__create_oauth_tokens.sql
│   │           ├── V3__create_health_records.sql
│   │           ├── V4__create_goals.sql
│   │           └── V5__create_ai_tables.sql
│   └── test/
│       ├── java/com/fitbitagent/
│       │   ├── controller/
│       │   ├── service/
│       │   ├── repository/
│       │   └── client/
│       └── resources/
│           └── application-test.yml
├── pom.xml
└── Dockerfile
```

### 各ディレクトリの役割

| ディレクトリ | 役割 | 配置するもの |
|------------|------|------------|
| `controller/` | HTTPリクエストの受付・レスポンス返却 | `@RestController` クラス |
| `service/` | ビジネスロジックの実装 | `@Service` クラス |
| `repository/` | データアクセス | `JpaRepository` インターフェース |
| `domain/entity/` | DBテーブルに対応するエンティティ | `@Entity` クラス |
| `domain/enums/` | ドメイン固有の列挙型 | GoalType, AdviceType, ChatRole |
| `client/fitbit/` | Fitbit API通信 | APIクライアント、レート制限、DTO |
| `client/claude/` | Claude API通信 | APIクライアント、プロンプト構築、DTO |
| `dto/request/` | APIリクエストボディの型定義 | リクエストDTO |
| `dto/response/` | APIレスポンスボディの型定義 | レスポンスDTO |
| `config/` | Spring設定クラス | `@Configuration` クラス |
| `exception/` | 例外クラス・グローバルハンドラー | カスタム例外、`@RestControllerAdvice` |
| `resources/prompts/` | AIプロンプトテンプレート | テキストファイル |
| `resources/db/migration/` | DBマイグレーション | Flyway SQLファイル |
| `test/` | テストコード | 本番コードと同じパッケージ構成 |

---

## 4. フロントエンド ディレクトリ構成

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ChartDetailPage.tsx
│   │   ├── GoalSettingPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── WeeklyReportPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── SettingsPage.tsx
│   ├── components/
│   │   ├── layout/
│   │   ├── dashboard/
│   │   ├── chat/
│   │   └── common/
│   ├── hooks/
│   ├── api/
│   ├── types/
│   └── utils/
├── public/
│   └── favicon.ico
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── eslint.config.js
└── Dockerfile
```

### 各ディレクトリの役割

| ディレクトリ | 役割 | 配置するもの |
|------------|------|------------|
| `pages/` | 画面単位のコンポーネント（ルーティング対応） | 1画面 = 1ファイル。画面IDと対応 |
| `components/layout/` | 共通レイアウト | Header, BottomNav, AuthLayout |
| `components/dashboard/` | ダッシュボード専用コンポーネント | SummaryCard, TrendChart 等 |
| `components/chat/` | チャット専用コンポーネント | ChatMessage, ChatInput |
| `components/common/` | 汎用UIコンポーネント | LoadingSpinner, ErrorMessage 等 |
| `hooks/` | カスタムフック | React Query ラッパー、状態管理 |
| `api/` | バックエンドAPI通信 | Axiosインスタンス、各APIモジュール |
| `types/` | TypeScript型定義 | APIレスポンス型、ドメイン型 |
| `utils/` | ユーティリティ関数 | 日付・数値フォーマット等 |

### コンポーネント配置ルール

| 条件 | 配置先 |
|------|-------|
| 1つの画面でのみ使用する | `pages/` 内にインライン定義、または同画面の `components/` サブディレクトリ |
| 複数画面で再利用する | `components/common/` |
| 特定ドメインに属する（例: ダッシュボード） | `components/{domain}/` |

---

## 5. 設定ファイル一覧

### 5.1 プロジェクトルート

| ファイル | 役割 |
|---------|------|
| `CLAUDE.md` | Claude Code のプロジェクト指示 |
| `.gitignore` | Git追跡除外ルール |
| `README.md` | プロジェクト概要・セットアップ手順 |

### 5.2 バックエンド

| ファイル | 役割 |
|---------|------|
| `pom.xml` | Maven依存関係・ビルド設定 |
| `Dockerfile` | Spring Bootコンテナ定義 |
| `application.yml` | 共通設定 |
| `application-dev.yml` | 開発環境設定 |
| `application-prod.yml` | 本番環境設定 |
| ~~`application-test.yml`~~ | ~~テスト環境設定~~ ※ 不要（テスト環境は用意しない） |

### 5.3 フロントエンド

| ファイル | 役割 |
|---------|------|
| `package.json` | npm依存関係・スクリプト定義 |
| `tsconfig.json` | TypeScript設定 |
| `vite.config.ts` | Viteビルド設定（プロキシ等） |
| `tailwind.config.js` | Tailwind CSS設定 |
| `eslint.config.js` | ESLint設定 |
| `Dockerfile` | React SPAコンテナ定義（ビルド→Nginx） |

### 5.4 インフラ

| ファイル | 役割 |
|---------|------|
| `docker/docker-compose.yml` | ローカル開発環境（PostgreSQL + アプリ） |
| `.github/workflows/ci.yml` | GitHub Actions CI/CD定義 |

---

## 6. モジュール分割方針

### 6.1 バックエンド・フロントエンド分離

```
fitbit-agent/
├── backend/     ← 独立したMavenプロジェクト
└── frontend/    ← 独立したnpmプロジェクト
```

- バックエンドとフロントエンドは**別プロセス**として起動する
- 開発時はViteのプロキシ機能でAPIリクエストをバックエンドに転送する
- 本番ではCloudFrontがルーティングを担う

### 6.2 バックエンドのモジュール方針

MVP段階では**単一Mavenモジュール**とする。

| 方針 | 理由 |
|------|------|
| マルチモジュール化しない | 機能数13のMVPには過剰。ビルド・設定の複雑性が不要 |
| パッケージで責務を分離 | レイヤードアーキテクチャのパッケージ構成で十分な分離を実現 |
| 将来の分割ポイント | `client/fitbit`, `client/claude` は独立ライブラリ化の候補 |

### 6.3 フロントエンドのモジュール方針

MVP段階では**単一SPAアプリケーション**とする。

| 方針 | 理由 |
|------|------|
| モノレポ構成にしない | 画面数8のMVPには不要 |
| ページ単位でコード分割 | React.lazy + Suspense による動的インポートで初回ロードを軽量化 |

---

## 更新履歴
- 2026-02-09: 初版作成
