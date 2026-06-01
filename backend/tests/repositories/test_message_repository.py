from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.models.message import Message
from backend.models.message_role import MessageRole
from backend.repositories.message_repository import MessageRepository

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
        MessageRepository(conn).get_all(chat_id=1)
        expected_sql = """
                SELECT id, chat_id, role, content, created_at
                FROM messages
                WHERE chat_id = %s
                ORDER BY created_at ASC
                """
        cursor.execute.assert_called_with(expected_sql, [1])

    def test_returns_message_list(self):
        conn, cursor = make_mock_conn()
        cursor.fetchall.return_value = [
            (1, 1, "user", "今日の歩数は？", CREATED_AT),
            (2, 1, "assistant", "8000歩です。", CREATED_AT),
        ]
        result = MessageRepository(conn).get_all(chat_id=1)
        assert len(result) == 2
        assert result[0].role == MessageRole.USER
        assert result[0].content == "今日の歩数は？"
        assert result[1].role == MessageRole.ASSISTANT
        assert result[1].content == "8000歩です。"

    def test_returns_empty_list_when_no_messages(self):
        conn, cursor = make_mock_conn()
        cursor.fetchall.return_value = []
        result = MessageRepository(conn).get_all(chat_id=1)
        assert result == []


class TestInsert:
    def test_insert_executes_correct_sql(self):
        conn, cursor = make_mock_conn()
        message = Message(chat_id=1, role=MessageRole.USER, content="今日の歩数は？")
        MessageRepository(conn).insert(message)
        expected_sql = """
                INSERT INTO messages (chat_id, role, content, created_at)
                VALUES (%s, %s, %s, NOW())
                """
        cursor.execute.assert_called_with(
            expected_sql, [1, MessageRole.USER, "今日の歩数は？"]
        )
        conn.commit.assert_called_once()

    def test_insert_assistant_message(self):
        conn, cursor = make_mock_conn()
        message = Message(chat_id=1, role=MessageRole.ASSISTANT, content="8000歩です。")
        MessageRepository(conn).insert(message)
        cursor.execute.assert_called_with(
            """
                INSERT INTO messages (chat_id, role, content, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
            [1, MessageRole.ASSISTANT, "8000歩です。"],
        )
