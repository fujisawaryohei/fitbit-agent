from backend.models.chat import Chat


class ChatRepository:
    def __init__(self, conn):
        self.conn = conn

    def list(self, user_id: int) -> list[Chat]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, title, created_at, updated_at
                FROM chats
                WHERE user_id = %s
                """,
                [user_id],
            )
            rows = cur.fetchall()
            return [
                Chat(
                    id=row[0],
                    user_id=row[1],
                    title=row[2],
                    created_at=row[3],
                    updated_at=row[4],
                )
                for row in rows
            ]

    def find_by_id(self, id: int) -> Chat | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, title, created_at, updated_at
                FROM chats
                WHERE id = %s
                """,
                [id],
            )
            row = cur.fetchone()
            if row is None:
                return None
            return Chat(
                id=row[0],
                user_id=row[1],
                title=row[2],
                created_at=row[3],
                updated_at=row[4],
            )

    def insert(self, chat: Chat) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chats (user_id, title, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                RETURNING id
                """,
                [chat.user_id, chat.title],
            )
            row = cur.fetchone()
        self.conn.commit()
        return row[0]

    def delete_by_id(self, id: int) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM chats WHERE id = %s
                """,
                [id],
            )
        self.conn.commit()
