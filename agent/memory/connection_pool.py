import os

from psycopg2.extensions import connection
from psycopg2.pool import SimpleConnectionPool

_pool: SimpleConnectionPool | None = None


def get_pool() -> SimpleConnectionPool:
    global _pool

    if _pool is None:
        _pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=os.getenv("PGVECTOR_DSN"))
    return _pool


def get_connection() -> connection:
    return get_pool().getconn()


def release_connection(conn: connection) -> None:
    get_pool().putconn(conn)
