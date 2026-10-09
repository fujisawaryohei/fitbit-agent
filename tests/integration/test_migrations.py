from collections.abc import Iterator

import psycopg2
import pytest

from tests.integration.conftest import run_alembic

APP_TABLES = {"users", "memories", "chats", "messages"}


def _existing_tables(dsn: str) -> set[str]:
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        return {row[0] for row in cur.fetchall()}


def _has_vector_extension(dsn: str) -> bool:
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        return cur.fetchone() is not None


@pytest.fixture
def db(db_env: str) -> Iterator[str]:
    """テスト後に必ず head へ戻す（ほかの統合テストが head を前提にするため）。"""
    try:
        yield db_env
    finally:
        run_alembic("upgrade", "head")


class TestMigrations:
    def test_upgrade_creates_tables_and_extension(self, db: str) -> None:
        run_alembic("upgrade", "head")

        assert APP_TABLES <= _existing_tables(db)
        assert _has_vector_extension(db)

    def test_downgrade_to_base_removes_everything(self, db: str) -> None:
        run_alembic("upgrade", "head")

        run_alembic("downgrade", "base")

        assert not (APP_TABLES & _existing_tables(db))
        assert not _has_vector_extension(db)

    def test_upgrade_again_after_downgrade(self, db: str) -> None:
        run_alembic("upgrade", "head")
        run_alembic("downgrade", "base")

        run_alembic("upgrade", "head")

        assert APP_TABLES <= _existing_tables(db)
        assert _has_vector_extension(db)

    def test_downgrade_one_step_removes_only_chat_tables(self, db: str) -> None:
        run_alembic("upgrade", "head")

        run_alembic("downgrade", "-1")

        tables = _existing_tables(db)
        assert not ({"chats", "messages"} & tables)
        assert {"users", "memories"} <= tables

    def test_upgrade_head_is_idempotent(self, db: str) -> None:
        run_alembic("upgrade", "head")

        run_alembic("upgrade", "head")

        assert APP_TABLES <= _existing_tables(db)
