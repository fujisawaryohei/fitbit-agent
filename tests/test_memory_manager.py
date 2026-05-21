from unittest.mock import MagicMock, patch

from memory.manager import save_memory, search_memories

DUMMY_EMBEDDING = [0.1] * 1024


def make_conn_mock(fetchall_return: list | None = None) -> MagicMock:
    cursor_mock = MagicMock()
    cursor_mock.__enter__ = lambda s: cursor_mock
    cursor_mock.__exit__ = MagicMock(return_value=False)
    cursor_mock.fetchall.return_value = fetchall_return or []
    conn_mock = MagicMock()
    conn_mock.cursor.return_value = cursor_mock
    return conn_mock


class TestSaveMemory:
    def test_executes_upsert(self) -> None:
        conn_mock = make_conn_mock()
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection") as mock_release:
            save_memory("session-1", "テスト内容")

        cursor_mock = conn_mock.cursor.return_value
        cursor_mock.execute.assert_called_once()
        sql = cursor_mock.execute.call_args[0][0]
        assert "INSERT INTO memories" in sql
        assert "ON CONFLICT" in sql
        conn_mock.commit.assert_called_once()
        mock_release.assert_called_once_with(conn_mock)

    def test_embedding_is_passed(self) -> None:
        conn_mock = make_conn_mock()
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING) as mock_embed, \
             patch("memory.manager.release_connection"):
            save_memory("session-1", "テスト内容")

        mock_embed.assert_called_once_with("テスト内容")
        params = conn_mock.cursor.return_value.execute.call_args[0][1]
        assert params[2] == DUMMY_EMBEDDING

    def test_releases_connection_on_error(self) -> None:
        conn_mock = make_conn_mock()
        conn_mock.cursor.return_value.execute.side_effect = Exception("DB error")
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection") as mock_release:
            save_memory("session-1", "テスト内容")

        mock_release.assert_called_once_with(conn_mock)


class TestSearchMemories:
    def test_returns_content_list(self) -> None:
        conn_mock = make_conn_mock(fetchall_return=[("記憶1",), ("記憶2",)])
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection"):
            result = search_memories("session-1", "クエリ")

        assert result == ["記憶1", "記憶2"]

    def test_cosine_similarity_query(self) -> None:
        conn_mock = make_conn_mock()
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection"):
            search_memories("session-1", "クエリ")

        sql = conn_mock.cursor.return_value.execute.call_args[0][0]
        assert "<=>" in sql
        assert "ORDER BY" in sql

    def test_returns_empty_on_db_error(self) -> None:
        conn_mock = make_conn_mock()
        conn_mock.cursor.return_value.execute.side_effect = Exception("DB error")
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection"):
            result = search_memories("session-1", "クエリ")

        assert result == []

    def test_releases_connection_on_error(self) -> None:
        conn_mock = make_conn_mock()
        conn_mock.cursor.return_value.execute.side_effect = Exception("DB error")
        with patch("memory.manager.get_connection", return_value=conn_mock), \
             patch("memory.manager.embed", return_value=DUMMY_EMBEDDING), \
             patch("memory.manager.release_connection") as mock_release:
            search_memories("session-1", "クエリ")

        mock_release.assert_called_once_with(conn_mock)
