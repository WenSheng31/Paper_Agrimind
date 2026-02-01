from sentence_transformers import SentenceTransformer

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def get_embedding(text: str) -> list[float]:
    model = _get_model()
    return model.encode(text).tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return model.encode(texts).tolist()
