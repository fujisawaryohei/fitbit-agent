from unittest.mock import MagicMock, patch

import pytest

from backend.config import connection_pool


@pytest.fixture(autouse=True)
def reset_pool(monkeypatch):
    monkeypatch.setattr(connection_pool, "_pool", None)


class TestGetPool:
    def test_creates_pool_with_dsn_from_env(self, monkeypatch):
        monkeypatch.setenv("PGVECTOR_DSN", "postgresql://u:p@host:5432/db")
        with patch.object(connection_pool, "SimpleConnectionPool") as pool_cls:
            pool = connection_pool.get_pool()

        pool_cls.assert_called_once_with(minconn=1, maxconn=5, dsn="postgresql://u:p@host:5432/db")
        assert pool is pool_cls.return_value

    def test_pool_is_created_only_once(self, monkeypatch):
        monkeypatch.setenv("PGVECTOR_DSN", "dsn")
        with patch.object(connection_pool, "SimpleConnectionPool") as pool_cls:
            first = connection_pool.get_pool()
            second = connection_pool.get_pool()

        assert first is second
        pool_cls.assert_called_once()


class TestConnections:
    def test_get_connection_takes_from_pool(self):
        pool = MagicMock()
        with patch.object(connection_pool, "get_pool", return_value=pool):
            conn = connection_pool.get_connection()

        assert conn is pool.getconn.return_value

    def test_release_connection_puts_back_to_pool(self):
        pool = MagicMock()
        conn = MagicMock()
        with patch.object(connection_pool, "get_pool", return_value=pool):
            connection_pool.release_connection(conn)

        pool.putconn.assert_called_once_with(conn)
