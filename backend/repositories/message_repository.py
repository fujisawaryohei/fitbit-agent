import psycopg2.extensions

from backend.models.message import Message
from backend.models.message_role import MessageRole


class MessageRepository:
    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self.conn = conn

    def get_all(self, chat_id: int) -> list[Message]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, chat_id, role, content, created_at
                FROM messages
                WHERE chat_id = %s
                ORDER BY created_at ASC
                """,
                [chat_id],
            )
            rows = cur.fetchall()
            return [
                Message(
                    id=row[0],
                    chat_id=row[1],
                    role=MessageRole(row[2]),
                    content=row[3],
                    created_at=row[4],
                )
                for row in rows
            ]

    def insert(self, message: Message) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (chat_id, role, content, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                [message.chat_id, message.role, message.content],
            )
        self.conn.commit()
