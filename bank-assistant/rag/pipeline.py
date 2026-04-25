from __future__ import annotations

from typing import Any, Dict, List

import ollama

from .prompts import SYSTEM_PROMPT, build_prompt
from .vector_store import RetrievedDoc, similarity_search


OLLAMA_MODEL = "mistral:7b"
TOP_K = 4


def _sources(docs: List[RetrievedDoc]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for d in docs:
        snippet = (d.text or "").strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:240].rstrip() + "…"
        out.append(
            {
                "id": d.id,
                "source": d.metadata.get("source") or d.metadata.get("url") or d.id,
                "distance": d.distance,
                "snippet": snippet,
            }
        )
    return out


def run(query: str) -> Dict[str, Any]:
    """
    Minimal RAG:
    - retrieve top 4 documents from Chroma
    - generate an answer with Ollama mistral:7b
    - return answer + sources
    """
    q = (query or "").strip()
    if not q:
        return {"answer": "Please enter a question.", "sources": []}

    docs = similarity_search(q, k=TOP_K)
    prompt = build_prompt(q, docs)

    try:
        response = ollama.generate(
            model=OLLAMA_MODEL,
            system=SYSTEM_PROMPT,
            prompt=prompt,
            stream=False,
        )
    except Exception as e:
        # Keep the pipeline resilient if Ollama isn't running or the model isn't pulled yet.
        msg = str(e).strip() or "Ollama error"
        hint = (
            f"LLM is unavailable ({msg}). "
            f"Make sure Ollama is running and the model is pulled: `ollama pull {OLLAMA_MODEL}`."
        )
        return {"answer": hint, "sources": _sources(docs)}

    answer = (response.get("response") or "").strip()
    if not answer:
        answer = "I couldn't generate an answer from the available information."

    return {"answer": answer, "sources": _sources(docs)}

