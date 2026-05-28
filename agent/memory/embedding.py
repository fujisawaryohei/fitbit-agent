from langchain_aws import BedrockEmbeddings

_embeddings: BedrockEmbeddings | None = None


def _get_embeddings() -> BedrockEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name="ap-northeast-1",
        )
    return _embeddings


def embed(text: str) -> list[float]:
    return _get_embeddings().embed_query(text)
