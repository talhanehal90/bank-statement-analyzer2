from __future__ import annotations

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts into vectors for ChromaDB.
    Returns a list of float vectors (lists) to keep dependencies minimal.
    """
    if not texts:
        return []
    vectors = _model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(query: str) -> List[float]:
    vecs = embed_texts([query])
    return vecs[0] if vecs else []

