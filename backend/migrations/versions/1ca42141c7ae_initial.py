"""initial

Revision ID: 1ca42141c7ae
Revises:
Create Date: 2026-05-24 11:38:06.290146

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1ca42141c7ae"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id          SERIAL PRIMARY KEY,
            session_id  TEXT        NOT NULL,
            content     TEXT        NOT NULL,
            embedding   vector(1024),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id               SERIAL PRIMARY KEY,
            fitbit_user_id   VARCHAR(255) UNIQUE NOT NULL,
            access_token     TEXT        NOT NULL,
            refresh_token    TEXT        NOT NULL,
            token_expires_at TIMESTAMPTZ NOT NULL,
            scope            TEXT        NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    pass


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS memories")
    op.execute("DROP EXTENSION IF EXISTS vector")
    pass
