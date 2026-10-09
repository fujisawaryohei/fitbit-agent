from unittest.mock import patch

import pytest

from agent.memory import embedding


@pytest.fixture(autouse=True)
def reset_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(embedding, "_embeddings", None)


class TestGetEmbeddings:
    def test_created_only_once_across_calls(self) -> None:
        with patch("agent.memory.embedding.BedrockEmbeddings") as mock_cls:
            first = embedding._get_embeddings()
            second = embedding._get_embeddings()

        assert first is second
        mock_cls.assert_called_once()

    def test_created_with_titan_model_and_region(self) -> None:
        with patch("agent.memory.embedding.BedrockEmbeddings") as mock_cls:
            embedding._get_embeddings()

        kwargs = mock_cls.call_args.kwargs
        assert kwargs["model_id"] == "amazon.titan-embed-text-v2:0"
        assert kwargs["region_name"] == "ap-northeast-1"


class TestEmbed:
    def test_returns_embed_query_result(self) -> None:
        with patch("agent.memory.embedding.BedrockEmbeddings") as mock_cls:
            mock_cls.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
            result = embedding.embed("こんにちは")

        assert result == [0.1, 0.2, 0.3]
        mock_cls.return_value.embed_query.assert_called_once_with("こんにちは")

    def test_repeated_embed_reuses_one_client(self) -> None:
        with patch("agent.memory.embedding.BedrockEmbeddings") as mock_cls:
            embedding.embed("a")
            embedding.embed("b")

        mock_cls.assert_called_once()
        assert mock_cls.return_value.embed_query.call_count == 2
