from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb

from .embeddings import embed_query, embed_texts


PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "banking_kb"


@dataclass(frozen=True)
class RetrievedDoc:
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=PERSIST_DIR)


def get_collection():
    client = _client()
    return client.get_or_create_collection(name=COLLECTION_NAME)


def add_documents(
    texts: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> int:
    """
    Minimal helper for loading a KB into Chroma.
    Not used by the pipeline automatically, but useful for seeding data.
    """
    if not texts:
        return 0
    if metadatas is not None and len(metadatas) != len(texts):
        raise ValueError("metadatas must be the same length as texts")
    if ids is not None and len(ids) != len(texts):
        raise ValueError("ids must be the same length as texts")

    collection = get_collection()
    embeddings = embed_texts(texts)

    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings,
    )
    return len(texts)


def similarity_search(
    query: str,
    k: int = 4,
    filter: Optional[Dict[str, Any]] = None,
) -> List[RetrievedDoc]:
    collection = get_collection()
    q_emb = embed_query(query)

    result = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"],
        where=filter,
    )

    ids: List[str] = (result.get("ids") or [[]])[0] or []
    docs: List[str] = (result.get("documents") or [[]])[0] or []
    metas: List[Dict[str, Any]] = (result.get("metadatas") or [[]])[0] or []
    dists: List[float] = (result.get("distances") or [[]])[0] or []

    out: List[RetrievedDoc] = []
    for i in range(min(len(ids), len(docs), len(metas), len(dists))):
        out.append(
            RetrievedDoc(
                id=str(ids[i]),
                text=str(docs[i]),
                metadata=metas[i] if isinstance(metas[i], dict) else {},
                distance=float(dists[i]),
            )
        )
    return out

