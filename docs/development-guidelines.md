# 開発ガイドライン: Fitbit Body Management AI Agent

## 目次
1. [はじめに](#1-はじめに)
2. [コーディング規約](#2-コーディング規約)
3. [命名規則](#3-命名規則)
4. [テスト方針](#4-テスト方針)
5. [Git運用ルール](#5-git運用ルール)
6. [コードレビュー基準](#6-コードレビュー基準)
7. [依存ライブラリ管理](#7-依存ライブラリ管理)

---

## 1. はじめに

### 1.1 本ドキュメントの目的
本ドキュメントは、開発チームが統一的なコード品質を維持するためのルールと慣例を定義する。

### 1.2 関連ドキュメント
| ドキュメント | ファイル |
|-------------|---------|
| アーキテクチャ設計書 | docs/architecture.md |
| リポジトリ定義書 | docs/repository-structure.md |
| チケット管理 | .steering/tasklist.md |
| 技術Q&A | .questions/question-{日付}.md |

---

## 2. コーディング規約

### 2.1 Java (バックエンド)

#### フォーマット
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html) に準拠
- インデント: スペース4つ
- 行の最大長: 120文字
- フォーマッターは `google-java-format` を使用

#### 基本ルール
- `var` はローカル変数で型が明白な場合にのみ使用可
- `Optional` は戻り値にのみ使用し、フィールド・引数には使用しない
- `null` を返すより `Optional` または空コレクションを返す
- フィールドインジェクション (`@Autowired`) は禁止、コンストラクタインジェクションを使用
- Lombokは `@Getter`, `@RequiredArgsConstructor`, `@Builder`, `@Slf4j` のみ許可

#### Controller規約
```java
// Good: レスポンス型を明示、バリデーション適用
@PostMapping("/goals")
public ResponseEntity<GoalResponse> createGoal(@Valid @RequestBody GoalCreateRequest request) {
    return ResponseEntity.status(HttpStatus.CREATED)
            .body(goalService.create(request));
}
```

#### Service規約
- `@Transactional` はService層のメソッドに付与
- 読み取り専用メソッドには `@Transactional(readOnly = true)` を使用

### 2.2 TypeScript / React (フロントエンド)

#### フォーマット
- Prettier + ESLint で統一
- インデント: スペース2つ
- セミコロン: あり
- クォート: シングルクォート

#### 基本ルール
- `any` 型の使用は禁止、必ず型を明示する
- コンポーネントは関数コンポーネント + フックで記述（クラスコンポーネント不可）
- `useEffect` 内の副作用は必ずクリーンアップ関数を返す
- イベントハンドラは `handle` プレフィックス（例: `handleSubmit`, `handleClick`）

#### コンポーネント規約
```tsx
// Good: Props型定義、デフォルトエクスポート
type SummaryCardProps = {
  title: string;
  value: number | null;
  unit: string;
  trend?: number;
};

const SummaryCard = ({ title, value, unit, trend }: SummaryCardProps) => {
  return (
    <div>
      <h3>{title}</h3>
      <p>{value !== null ? `${value} ${unit}` : '--'}</p>
    </div>
  );
};

export default SummaryCard;
```

---

## 3. 命名規則

### 3.1 Java

| 対象 | 規則 | 例 |
|------|------|-----|
| クラス名 | UpperCamelCase | `GoalService`, `FitbitApiClient` |
| メソッド名 | lowerCamelCase | `createGoal()`, `syncBodyRecords()` |
| 変数名 | lowerCamelCase | `targetWeight`, `dailySteps` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_SYNC_DAYS` |
| パッケージ名 | 小文字のみ | `com.fitbitagent.controller` |
| Enumの値 | UPPER_SNAKE_CASE | `CALORIES_BURNED`, `DAILY` |

#### クラスのサフィックス規則

| レイヤー | サフィックス | 例 |
|---------|------------|-----|
| Controller | `Controller` | `GoalController` |
| Service | `Service` | `GoalService` |
| Repository | `Repository` | `GoalRepository` |
| Entity | なし | `Goal`, `User` |
| リクエストDTO | `Request` | `GoalCreateRequest` |
| レスポンスDTO | `Response` | `GoalResponse` |
| 外部APIクライアント | `Client` | `FitbitApiClient` |
| 設定クラス | `Config` | `SecurityConfig` |
| 例外クラス | `Exception` | `FitbitApiException` |

### 3.2 TypeScript / React

| 対象 | 規則 | 例 |
|------|------|-----|
| コンポーネント | UpperCamelCase | `SummaryCard`, `ChatInput` |
| カスタムフック | `use` + UpperCamelCase | `useAuth`, `useDashboard` |
| 関数・変数 | lowerCamelCase | `fetchGoals`, `isLoading` |
| 型・インターフェース | UpperCamelCase | `GoalResponse`, `DashboardSummary` |
| 定数 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| ファイル名（コンポーネント） | UpperCamelCase.tsx | `SummaryCard.tsx` |
| ファイル名（その他） | lowerCamelCase.ts | `dashboardApi.ts`, `useAuth.ts` |

### 3.3 API エンドポイント

| 規則 | 例 |
|------|-----|
| 名詞の複数形を使用 | `/api/goals`, `/api/chat/messages` |
| ケバブケース | `/api/advice/daily`, `/api/dashboard/summary` |
| ネストは最大2階層 | `/api/chat/sessions/{id}/messages` |
| 動詞はHTTPメソッドで表現 | `POST /api/sync`（`/api/do-sync` ではない） |

### 3.4 データベース

| 対象 | 規則 | 例 |
|------|------|-----|
| テーブル名 | snake_case（複数形） | `body_records`, `chat_messages` |
| カラム名 | snake_case | `weight_kg`, `record_date` |
| 主キー | `id` | すべてのテーブル共通 |
| 外部キー | `{参照テーブル単数形}_id` | `user_id` |
| インデックス名 | `idx_{テーブル}_{カラム}` | `idx_body_records_user_date` |
| マイグレーション | `V{番号}__{説明}.sql` | `V1__create_users.sql` |

---

## 4. テスト方針

### 4.1 テスト種別

| 種別 | 対象 | ツール | カバレッジ目標 |
|------|------|-------|-------------|
| 単体テスト | Service, Client, ユーティリティ | JUnit 5 + Mockito | 80%以上 |
| 結合テスト | Repository (DB) | Testcontainers + PostgreSQL | 主要クエリ全件 |
| APIテスト | Controller (エンドポイント) | MockMvc | 全エンドポイント |
| フロントエンド単体テスト | コンポーネント、フック | Vitest + React Testing Library | 主要コンポーネント |

### 4.2 テストの原則

- **テストは本番コードと同じパッケージ構成**にする
- **外部API呼び出しは必ずモック**する（Fitbit API, Claude API）
- テストメソッド名は `should_期待結果_when_条件` 形式
- 1テストメソッドで1つの振る舞いのみ検証

```java
// Good: テストメソッド名の例
@Test
void should_returnDailySummary_when_dataExists() { ... }

@Test
void should_throwException_when_rateLimitExceeded() { ... }
```

### 4.3 テスト実行

```bash
# バックエンド
cd backend && mvn test              # 単体テスト
cd backend && mvn verify            # 単体 + 結合テスト

# フロントエンド
cd frontend && npm test             # 単体テスト
cd frontend && npm run test:ci      # CI用（カバレッジ出力）
```

---

## 5. Git運用ルール

### 5.1 ブランチ戦略

**GitHub Flow** を採用する。

```
main ─────────────────────────────────────────→
       ↑              ↑              ↑
       │ feature/FR-001-oauth-login  │
       │              │              │
       └──────────────┘ fix/fix-sync-error
                                     │
                                     └──────→
```

| ブランチ | 用途 | 命名規則 |
|---------|------|---------|
| `main` | 本番リリース可能な状態を維持 | - |
| `feature/*` | 新機能開発 | `feature/{機能ID}-{説明}` |
| `fix/*` | バグ修正 | `fix/{説明}` |
| `docs/*` | ドキュメント変更 | `docs/{説明}` |

### 5.2 コミットメッセージ規約

**Conventional Commits** に準拠する。言語は英語。

```
<type>(<scope>): <description>

[optional body]
```

#### Type一覧

| Type | 用途 | 例 |
|------|------|-----|
| `feat` | 新機能 | `feat(auth): add Fitbit OAuth2.0 login` |
| `fix` | バグ修正 | `fix(sync): handle rate limit error correctly` |
| `refactor` | リファクタリング | `refactor(service): extract common validation logic` |
| `test` | テスト追加・修正 | `test(goal): add unit tests for GoalService` |
| `docs` | ドキュメント | `docs: update architecture design` |
| `chore` | ビルド・設定変更 | `chore: update Spring Boot to 3.x.x` |
| `style` | コードフォーマット | `style: apply google-java-format` |

#### Scope一覧

| Scope | 対象 |
|-------|------|
| `auth` | 認証・ユーザー管理 (FR-001〜003) |
| `sync` | データ同期 (FR-010〜011) |
| `dashboard` | ダッシュボード (FR-020〜022) |
| `goal` | 目標設定 (FR-030〜031) |
| `advice` | AIアドバイス (FR-040〜041) |
| `chat` | チャット (FR-042) |
| `infra` | インフラ・CI/CD |
| `deps` | 依存関係更新 |

### 5.3 Pull Request ルール

- PRタイトルはコミットメッセージと同じ形式
- PRの粒度: 1つの機能ID（FR-xxx）または1つのバグ修正を1PRとする
- PRテンプレート:
  ```
  ## Summary
  - 変更内容の箇条書き

  ## Related
  - 機能ID: FR-xxx

  ## Test plan
  - [ ] テスト内容
  ```
- self-merge可（MVPフェーズ、個人開発のため）

---

## 6. コードレビュー基準

### 6.1 レビュー観点

| 観点 | チェック内容 |
|------|------------|
| 機能性 | 要件通りに動作するか |
| レイヤー違反 | Controller→Service→Repository の依存方向が守られているか |
| セキュリティ | SQLインジェクション、XSS、機密情報のハードコーディングがないか |
| エラーハンドリング | 外部API呼び出しが適切にtry-catchされているか |
| テスト | 変更に対応するテストが追加されているか |
| 命名 | 本ドキュメントの命名規則に準拠しているか |

### 6.2 レビュー不要の変更

- ドキュメントのみの修正
- フォーマット変更のみ（`style` タイプのコミット）
- 依存バージョンのパッチアップデート

---

## 7. 依存ライブラリ管理

### 7.1 バックエンド (Maven)

#### バージョン管理方針

| 方針 | 説明 |
|------|------|
| Spring Boot BOM | Spring関連はBOMでバージョン統一 |
| メジャーバージョン | 検証してから手動アップデート |
| マイナー/パッチ | 月次で `mvn versions:display-dependency-updates` で確認 |

#### 許可する依存の範囲

| カテゴリ | 許可 | 確認が必要 |
|---------|------|----------|
| Spring公式モジュール | 自由に追加可 | - |
| Apache Commons系 | 自由に追加可 | - |
| 認知度の高いOSS | - | ライセンス確認後に追加 |
| 個人開発のOSS | 非推奨 | チーム合意が必要 |

### 7.2 フロントエンド (npm)

#### バージョン管理方針

| 方針 | 説明 |
|------|------|
| `package-lock.json` | 必ずコミットする |
| メジャーバージョン | 検証してから手動アップデート |
| マイナー/パッチ | 月次で `npm outdated` で確認 |
| `devDependencies` | ビルドに不要なツールは `devDependencies` に分類 |

### 7.3 セキュリティ

- `npm audit` / `mvn dependency-check:check` をCIで実行
- Critical/High の脆弱性が検出された場合はビルドを失敗させる

---

## 更新履歴
- 2026-02-09: 初版作成
