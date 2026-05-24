from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.user import User
from app.repositories.user_repository import UserRepository

EXPIRES_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def make_mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cursor
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


class TestFindByFitbitUserId:
    def test_find_executes_correct_sql(self, make_mock_conn):
        conn, cursor = make_mock_conn
        user_repository = UserRepository(conn)
        user_repository.find_by_fitbit_user_id(fitbit_user_id="abc123")
        exptected_sql = """
                SELECT id, fitbit_user_id, access_token, refresh_token, token_expires_at, scope, created_at, updated_at
                FROM users
                WHERE fitbit_user_id = %s
                """
        cursor.execute.assert_called_with(exptected_sql, ["abc123"])

    def test_returns_none_when_not_found(self, make_mock_conn):
        conn, cursor = make_mock_conn
        cursor.fetchone.return_value = None

        user_repository = UserRepository(conn)
        result = user_repository.find_by_fitbit_user_id(fitbit_user_id="abc123")

        assert result is None


class TestUpsert:
    def test_upsert_correct_sql(self, make_mock_conn):
        conn, cursor = make_mock_conn
        user = User(
            fitbit_user_id="abc123",
            access_token="access",
            refresh_token="refresh",
            token_expires_at=EXPIRES_AT,
            scope="activity",
        )
        user_repository = UserRepository(conn)
        user_repository.upsert(user)
        exptected_sql = """
                INSERT INTO users (fitbit_user_id, access_token,
                refresh_token, token_expires_at, scope, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (fitbit_user_id) DO UPDATE SET
                    access_token     = EXCLUDED.access_token,
                    refresh_token    = EXCLUDED.refresh_token,
                    token_expires_at = EXCLUDED.token_expires_at,
                    scope            = EXCLUDED.scope,
                    updated_at       = NOW();
                """
        cursor.execute.assert_called_with(
            exptected_sql,
            ["abc123", "access", "refresh", EXPIRES_AT, "activity"],
        )


class TestUpdateTokens:
    def test_update_tokens_correct_sql(self, make_mock_conn):
        conn, cursor = make_mock_conn
        user_repository = UserRepository(conn)
        user_repository.update_tokens(
            fitbit_user_id="abc123",
            access_token="new_access",
            refresh_token="new_refresh",
            token_expires_at=EXPIRES_AT,
        )
        exptected_sql = """
            UPDATE users SET
                access_token     = %s,
                refresh_token    = %s,
                token_expires_at = %s,
                updated_at       = NOW()
            WHERE fitbit_user_id = %s
        """
        cursor.execute.assert_called_with(
            exptected_sql,
            ["new_access", "new_refresh", EXPIRES_AT, "abc123"],
        )
