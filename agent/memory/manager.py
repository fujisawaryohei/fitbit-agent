import logging

from agent.memory.embedding import embed
from app.config.connection_pool import get_connection, release_connection

logger = logging.getLogger(__name__)


def save_memory(session_id: str, content: str) -> None:
    conn = get_connection()
    try:
        embedding = embed(content)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memories (session_id, content, embedding)
                VALUES (%s, %s, %s::vector)
                """,
                (session_id, content, embedding),
            )
            cur.execute(
                """
                DELETE FROM memories
                WHERE session_id = %s
                AND id NOT IN (
                    SELECT id FROM memories
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 50
                )
                """,
                (session_id, session_id),
            )
        conn.commit()
    except Exception:
        logger.error("save_memory failed", exc_info=True)
    finally:
        release_connection(conn)


def search_memories(session_id: str, query: str, limit: int = 3) -> list[str]:
    conn = get_connection()
    try:
        query_embedding = embed(query)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content
                FROM memories
                WHERE session_id = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (session_id, query_embedding, limit),
            )
            return [row[0] for row in cur.fetchall()]
    except Exception:
        logger.error("search_memories failed", exc_info=True)
        return []
    finally:
        release_connection(conn)
