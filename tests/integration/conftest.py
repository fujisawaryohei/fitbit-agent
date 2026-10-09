"""本物の postgres（pgvector）を相手にする統合テストの共通 fixture。

`TEST_PGVECTOR_DSN` が無いときは、このディレクトリのテストを全部 skip する。
"""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg2
import psycopg2.extensions
import pytest
from alembic import command
from alembic.config import Config

from backend.config import connection_pool

TEST_DSN_ENV = "TEST_PGVECTOR_DSN"
ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
TABLES = ("messages", "chats", "memories", "users")


def make_alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def run_alembic(action: str, revision: str) -> None:
    """alembic の upgrade / downgrade を流す。接続先は env.py が PGVECTOR_DSN から読む。"""
    getattr(command, action)(make_alembic_config(), revision)


@pytest.fixture(autouse=True)
def require_test_dsn() -> None:
    if not os.getenv(TEST_DSN_ENV):
        pytest.skip(f"{TEST_DSN_ENV} が未設定のため統合テストを skip する")


@pytest.fixture(scope="session")
def test_dsn() -> str:
    dsn = os.getenv(TEST_DSN_ENV)
    if not dsn:
        pytest.skip(f"{TEST_DSN_ENV} が未設定のため統合テストを skip する")
    return dsn


@pytest.fixture
def db_env(test_dsn: str, monkeypatch: pytest.MonkeyPatch) -> str:
    """alembic の env.py と接続プールが読む PGVECTOR_DSN をテスト用 DB に向ける。"""
    monkeypatch.setenv("PGVECTOR_DSN", test_dsn)
    return test_dsn


@pytest.fixture
def migrated_db(db_env: str) -> str:
    """head まで upgrade 済みの空の DB（テーブルは TRUNCATE 済み）。"""
    run_alembic("upgrade", "head")
    with psycopg2.connect(db_env) as conn, conn.cursor() as cur:
        cur.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
    return db_env


@pytest.fixture
def conn(migrated_db: str) -> Iterator[psycopg2.extensions.connection]:
    connection = psycopg2.connect(migrated_db)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def pool(migrated_db: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """get_connection() が使うグローバルのプールを、テスト用 DB 向けに作り直す。"""
    monkeypatch.setattr(connection_pool, "_pool", None)
    try:
        yield
    finally:
        created = connection_pool._pool
        if created is not None:
            created.closeall()
