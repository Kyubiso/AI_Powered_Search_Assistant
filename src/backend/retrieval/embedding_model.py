from sentence_transformers import SentenceTransformer


DEFAULT_EMBEDDING_MODEL = "NeuML/pubmedbert-base-embeddings"

_MODEL_CACHE: dict[str, SentenceTransformer] = {}


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    model = _MODEL_CACHE.get(model_name)
    if model is None:
        model = SentenceTransformer(model_name)
        _MODEL_CACHE[model_name] = model
    return model


def embed_text(model: SentenceTransformer, text: str) -> list[float]:
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()
