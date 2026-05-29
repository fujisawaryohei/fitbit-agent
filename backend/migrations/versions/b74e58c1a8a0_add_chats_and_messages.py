"""add_chats_and_messages

Revision ID: b74e58c1a8a0
Revises: 1ca42141c7ae
Create Date: 2026-05-29 02:52:49.794340

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b74e58c1a8a0"
down_revision: Union[str, Sequence[str], None] = "1ca42141c7ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title      TEXT          NOT NULL,
            created_at TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         SERIAL PRIMARY KEY,
            chat_id    INTEGER       NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            role       VARCHAR(20)   NOT NULL,
            content    TEXT          NOT NULL,
            created_at TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS chats")
