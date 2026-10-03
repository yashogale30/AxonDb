import numpy as np

from .config import EMBED_MODEL, QUERY_PREFIX

_model = None


def get_model():
    """Load the model once, the first time it is needed."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed(text):
    """One sentence in, one normalised vector out."""
    vec = get_model().encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype=np.float32)


def embed_many(texts):
    texts = list(texts)
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    vecs = get_model().encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def embed_query(text):
    """Questions get a prefix for models trained that way. Stored text does not."""
    return embed(QUERY_PREFIX + text)


def similarities(query_vec, matrix):
    """Similarity of one vector against many. Higher means closer in meaning."""
    if matrix.shape[0] == 0:
        return np.zeros(0, dtype=np.float32)
    return matrix @ query_vec