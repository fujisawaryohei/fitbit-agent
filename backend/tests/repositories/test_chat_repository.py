from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.models.chat import Chat
from backend.repositories.chat_repository import ChatRepository

CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cursor
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


class TestList:
    def test_list_executes_correct_sql(self):
        conn, cursor = make_mock_conn()
        cursor.fetchall.return_value = []
        ChatRepository(conn).list(user_id=1)
        expected_sql = """
                SELECT id, user_id, title, created_at, updated_at
                FROM chats
                WHERE user_id = %s
                """
        cursor.execute.assert_called_with(expected_sql, [1])

    def test_returns_chat_list(self):
        conn, cursor = make_mock_conn()
        cursor.fetchall.return_value = [
            (1, 1, "チャット1", CREATED_AT, CREATED_AT),
            (2, 1, "チャット2", CREATED_AT, CREATED_AT),
        ]
        result = ChatRepository(conn).list(user_id=1)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].title == "チャット1"
        assert result[1].id == 2

    def test_returns_empty_list_when_no_chats(self):
        conn, cursor = make_mock_conn()
        cursor.fetchall.return_value = []
        result = ChatRepository(conn).list(user_id=1)
        assert result == []


class TestFindById:
    def test_find_executes_correct_sql(self):
        conn, cursor = make_mock_conn()
        cursor.fetchone.return_value = None
        ChatRepository(conn).find_by_id(id=1)
        expected_sql = """
                SELECT id, user_id, title, created_at, updated_at
                FROM chats
                WHERE id = %s
                """
        cursor.execute.assert_called_with(expected_sql, [1])

    def test_returns_chat_when_found(self):
        conn, cursor = make_mock_conn()
        cursor.fetchone.return_value = (1, 1, "チャット1", CREATED_AT, CREATED_AT)
        result = ChatRepository(conn).find_by_id(id=1)
        assert result is not None
        assert result.id == 1
        assert result.title == "チャット1"

    def test_returns_none_when_not_found(self):
        conn, cursor = make_mock_conn()
        cursor.fetchone.return_value = None
        result = ChatRepository(conn).find_by_id(id=999)
        assert result is None


class TestInsert:
    def test_insert_executes_correct_sql(self):
        conn, cursor = make_mock_conn()
        cursor.fetchone.return_value = (42,)
        chat = Chat(user_id=1, title="チャット1")
        ChatRepository(conn).insert(chat)
        expected_sql = """
                INSERT INTO chats (user_id, title, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                RETURNING id
                """
        cursor.execute.assert_called_with(expected_sql, [1, "チャット1"])
        conn.commit.assert_called_once()

    def test_insert_returns_chat_id(self):
        conn, cursor = make_mock_conn()
        cursor.fetchone.return_value = (42,)
        chat = Chat(user_id=1, title="チャット1")
        result = ChatRepository(conn).insert(chat)
        assert result == 42


class TestDeleteById:
    def test_delete_executes_correct_sql(self):
        conn, cursor = make_mock_conn()
        ChatRepository(conn).delete_by_id(id=1)
        expected_sql = """
                DELETE FROM chats WHERE id = %s
                """
        cursor.execute.assert_called_with(expected_sql, [1])
        conn.commit.assert_called_once()
