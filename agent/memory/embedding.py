from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")
    return _model


def embed(text: str) -> list[float]:
    model = get_embedding_model()
    result = model.encode(text, normalize_embeddings=True)
    return result.tolist()
