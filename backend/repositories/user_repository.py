from datetime import datetime

from backend.models.user import User


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def find_by_fitbit_user_id(self, fitbit_user_id: str) -> User | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, fitbit_user_id, access_token, refresh_token, token_expires_at, scope, created_at, updated_at
                FROM users
                WHERE fitbit_user_id = %s
                """,
                [fitbit_user_id],
            )
            row = cur.fetchone()
            if row is None:
                return None
            return User(
                id=row[0],
                fitbit_user_id=row[1],
                access_token=row[2],
                refresh_token=row[3],
                token_expires_at=row[4],
                scope=row[5],
                created_at=row[6],
                updated_at=row[7],
            )

    def upsert(self, user: User) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (fitbit_user_id, access_token,
                refresh_token, token_expires_at, scope, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (fitbit_user_id) DO UPDATE SET
                    access_token     = EXCLUDED.access_token,
                    refresh_token    = EXCLUDED.refresh_token,
                    token_expires_at = EXCLUDED.token_expires_at,
                    scope            = EXCLUDED.scope,
                    updated_at       = NOW();
                """,
                [
                    user.fitbit_user_id,
                    user.access_token,
                    user.refresh_token,
                    user.token_expires_at,
                    user.scope,
                ],
            )
        self.conn.commit()

    def update_tokens(
        self,
        fitbit_user_id: str,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
            UPDATE users SET
                access_token     = %s,
                refresh_token    = %s,
                token_expires_at = %s,
                updated_at       = NOW()
            WHERE fitbit_user_id = %s
        """,
                [access_token, refresh_token, token_expires_at, fitbit_user_id],
            )
        self.conn.commit()
