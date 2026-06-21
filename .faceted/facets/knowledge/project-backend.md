# Knowledge: project-backend (fitbit-agent)

- **バックエンド**: FastAPI (Python 3.13)、`backend/` 配下
- **DB**: PostgreSQL + pgvector、Alembic でマイグレーション管理
- **DI**: `dependency-injector`（`backend/containers.py` の `Container` クラス）
- **テスト**: pytest（`uv run pytest`）
- **パッケージ管理**: `uv`。**`python3` 直接呼び出し禁止、必ず `uv run python`**

## ディレクトリ
```
backend/
├── containers.py    # DI コンテナ
├── controllers/     # FastAPI ルーター（@inject + Depends(Provide[...])）
├── models/          # ドメインモデル（ORM なし、純粋 Python クラス）
├── repositories/    # リポジトリ（psycopg2 + 生 SQL）
├── schemas/         # Pydantic スキーマ
├── services/        # サービス層
├── config/          # 設定（connection_pool.py）
├── migrations/      # Alembic
└── tests/           # conftest.py に共通 container fixture
```

## 主要パターン

### エンドポイント（@inject + Cookie 認証）
```python
@router.get("/example")
@inject
def example(
    fitbit_user_id: str | None = Cookie(default=None),
    user_repo: UserRepository = Depends(Provide[Container.user_repo]),
):
    if fitbit_user_id is None:
        raise HTTPException(status_code=401, detail="認証が必要です。...")
    user = user_repo.find_by_fitbit_user_id(fitbit_user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません。...")
```

### テスト（container.override）
```python
def test_xxx(self, container):  # conftest.py の fixture
    mock_repo = MagicMock()
    with container.user_repo.override(mock_repo):
        client = TestClient(_app)
        response = client.get("/example")
```

### リポジトリ（psycopg2 + 生 SQL）
```python
class ExampleRepository:
    def __init__(self, conn) -> None:
        self.conn = conn
    def find_by_id(self, id: int):
        with self.conn.cursor() as cur:
            cur.execute("SELECT ... FROM ... WHERE id = %s", [id])
            row = cur.fetchone()
```

## 検証コマンド
- 全テスト: `uv run pytest backend/tests/ -q`
- LLM 依存テスト除外時: `uv run pytest backend/tests/ agent/tests/ --ignore=agent/tests/test_planning_tools_llm.py -q`
