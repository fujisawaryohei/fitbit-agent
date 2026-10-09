from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import psycopg2
import psycopg2.extensions
import pytest

from agent.memory.manager import save_memory, search_memories

DIMENSION = 1024
MEMORY_CAP = 50


def vec(*weights: tuple[int, float]) -> list[float]:
    """指定した次元だけ値を持つ 1024 次元のベクトル（残りは 0）。"""
    values = [0.0] * DIMENSION
    for index, weight in weights:
        values[index] = weight
    return values


# クエリ vec((0, 1.0)) とのコサイン類似度: CLOSE=1.0 > NEAR=0.8 > FAR=0.0
CLOSE = vec((0, 1.0))
NEAR = vec((0, 0.8), (1, 0.6))
FAR = vec((1, 1.0))
QUERY = vec((0, 1.0))


@pytest.fixture
def fake_embed() -> Iterator[MagicMock]:
    """決まったテキスト → 決まったベクトル。未知のテキストは FAR を返す。"""
    table = {"close": CLOSE, "near": NEAR, "far": FAR, "query": QUERY}
    with patch("agent.memory.manager.embed", side_effect=lambda t: table.get(t, FAR)) as m:
        yield m


def fetch_all(conn: psycopg2.extensions.connection) -> list[tuple[str, str]]:
    with conn.cursor() as cur:
        cur.execute("SELECT session_id, content FROM memories ORDER BY id")
        return [(row[0], row[1]) for row in cur.fetchall()]


@pytest.mark.usefixtures("pool", "fake_embed")
class TestSaveMemory:
    def test_inserts_row_with_embedding(self, conn: psycopg2.extensions.connection) -> None:
        save_memory("s1", "close")

        assert fetch_all(conn) == [("s1", "close")]
        with conn.cursor() as cur:
            cur.execute("SELECT vector_dims(embedding), embedding::text FROM memories")
            row = cur.fetchone()
        assert row is not None
        assert row[0] == DIMENSION
        assert row[1].startswith("[1,0,0")

    def test_keeps_only_latest_50_per_session(self, conn: psycopg2.extensions.connection) -> None:
        save_memory("other", "other-0")
        for i in range(MEMORY_CAP + 2):
            save_memory("s1", f"m{i}")

        rows = fetch_all(conn)
        s1 = [content for session, content in rows if session == "s1"]

        assert len(s1) == MEMORY_CAP
        assert "m0" not in s1 and "m1" not in s1
        assert s1[0] == "m2" and s1[-1] == f"m{MEMORY_CAP + 1}"
        assert ("other", "other-0") in rows

    def test_failure_does_not_raise_and_saves_nothing(
        self, conn: psycopg2.extensions.connection, fake_embed: MagicMock
    ) -> None:
        fake_embed.side_effect = None
        fake_embed.return_value = [0.0] * 3  # 次元違いで INSERT が失敗する

        save_memory("s1", "wrong-dimension")

        assert fetch_all(conn) == []


@pytest.mark.usefixtures("pool", "fake_embed")
class TestSearchMemories:
    def _seed(self, conn: psycopg2.extensions.connection) -> None:
        save_memory("s1", "far")
        save_memory("s1", "close")
        save_memory("s1", "near")

    def test_returns_contents_in_similarity_order(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        self._seed(conn)

        assert search_memories("s1", "query", limit=3) == ["close", "near", "far"]

    def test_respects_limit(self, conn: psycopg2.extensions.connection) -> None:
        self._seed(conn)

        assert search_memories("s1", "query", limit=2) == ["close", "near"]

    def test_default_limit_is_three(self, conn: psycopg2.extensions.connection) -> None:
        self._seed(conn)
        save_memory("s1", "far-2")

        result = search_memories("s1", "query")

        assert result[:2] == ["close", "near"]
        assert len(result) == 3

    def test_does_not_return_other_sessions_memories(
        self, conn: psycopg2.extensions.connection
    ) -> None:
        save_memory("s1", "far")
        save_memory("s2", "close")

        assert search_memories("s1", "query") == ["far"]
        assert search_memories("s2", "query") == ["close"]

    def test_unknown_session_returns_empty(self, conn: psycopg2.extensions.connection) -> None:
        self._seed(conn)

        assert search_memories("nobody", "query") == []
