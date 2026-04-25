from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import ollama

from rag.prompts import SYSTEM_PROMPT
from rag.vector_store import RetrievedDoc, similarity_search
from services.bank_service import detect_bank_from_message
from services.fallback_service import FallbackService
from services.query_router import QueryRouter, QueryType
from services.web_search_service import WebSearchService


def assess_rag_confidence(docs: List[RetrievedDoc], query: str) -> float:
    if not docs:
        return 0.0
    if len(docs) < 3:
        return 0.4

    ql = (query or "").lower()
    entity_hints = ["ceo", "chairman", "md", "managing director", "policy rate", "kibor"]
    if any(h in ql for h in entity_hints):
        found_hint = False
        for d in docs:
            tl = (d.text or "").lower()
            if any(h in tl for h in entity_hints):
                found_hint = True
                break
        if not found_hint:
            return 0.3

    return 0.8


def build_merged_context(rag_context: str, web_context: str, news_context: str) -> str:
    return (
        "KNOWLEDGE BASE CONTEXT (from official bank websites):\n"
        f"{rag_context}\n\n"
        "LIVE WEB SEARCH RESULTS (current information):\n"
        f"{web_context}\n\n"
        "LIVE NEWS RESULTS (recent updates):\n"
        f"{news_context}\n"
    )


def _format_rag_context(docs: List[RetrievedDoc]) -> str:
    if not docs:
        return ""
    parts: list[str] = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source") or d.metadata.get("url") or d.id
        parts.append(f"[KB {i}] Source: {src}\n{d.text}")
    return "\n\n".join(parts)


def _sources_from_docs(docs: List[RetrievedDoc], limit: int = 2) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for d in docs[:limit]:
        url = str(d.metadata.get("source") or d.metadata.get("url") or "")
        snippet = (d.text or "").strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:240].rstrip() + "…"
        out.append({"url": url, "snippet": snippet})
    return out


def llm_generate(message: str, merged_context: str, session_id: str | None = None) -> str:
    prompt = (
        f"{merged_context}\n\n"
        f"Based on the above context, answer this question: {message}\n\n"
        "Important:\n"
        "- Prioritize Knowledge Base context for product/service details\n"
        "- Prioritize Live Web Search for current rates, leadership, news\n"
        "- If sources conflict, mention both and note which is more recent\n"
        "- Always cite where the info came from (knowledge base or web search)\n"
    )
    resp = ollama.generate(model="mistral:7b", system=SYSTEM_PROMPT, prompt=prompt, stream=False)
    return (resp.get("response") or "").strip()


async def get_response(session_id: str | None, message: str, bank_filter: str | None = None) -> Dict[str, Any]:
    # STEP 1: Detect bank from message if not explicitly provided
    bank_slug = bank_filter or detect_bank_from_message(message)

    # STEP 2: Route the query
    query_router = QueryRouter()
    routing = query_router.route(message)

    web_search_service = WebSearchService()
    fallback_service = FallbackService()

    # STEP 3: Try fallback knowledge FIRST for leadership queries
    if routing["query_type"] == QueryType.LEADERSHIP and bank_slug:
        fallback_answer = fallback_service.answer_leadership_query(message, bank_slug)
        if fallback_answer:
            web_results = web_search_service.search(message, bank_name=bank_slug, max_results=3)
            web_context = web_search_service.format_results_as_context(web_results)
            combined_context = (
                "LEADERSHIP DATA (authoritative; use this directly in the answer):\n"
                f"{fallback_answer}\n\n"
                "Additional Web Info (may be newer; verify if conflicting):\n"
                f"{web_context}"
            )
            # We still run generation to keep the chain consistent, but we *return* the
            # fallback answer to avoid fabricating websites/helplines.
            _ = llm_generate(message, combined_context, session_id)
            return {"response": fallback_answer, "sources": []}

    # STEP 4: Try RAG retrieval
    rag_docs: List[RetrievedDoc] = []
    if routing["use_rag"]:
        rag_docs = similarity_search(
            message,
            k=8,
            filter={"bank_name": bank_slug} if bank_slug else None,
        )

    # STEP 5: Assess RAG confidence
    rag_confidence = assess_rag_confidence(rag_docs, message)

    # STEP 6: Web search if needed
    web_context = ""
    if routing["use_web_search"] or rag_confidence < 0.4:
        web_results = web_search_service.search(message, bank_name=bank_slug)
        web_context = web_search_service.format_results_as_context(web_results)

    # If this looks like an SBP policy-rate question and web search returned nothing,
    # use fallback knowledge rather than hallucinating.
    if (
        not web_context
        and "sbp" in (message or "").lower()
        and ("policy rate" in (message or "").lower() or "rate" in (message or "").lower())
    ):
        sbp_fallback = fallback_service.answer_sbp_policy_rate()
        if sbp_fallback:
            return {"response": sbp_fallback, "sources": []}

    # STEP 7: News search if needed
    news_context = ""
    if routing["use_news_search"]:
        news_results = web_search_service.search_news(message, bank_name=bank_slug)
        news_context = web_search_service.format_results_as_context(news_results)

    # STEP 8: Build merged context
    rag_context = _format_rag_context(rag_docs)
    merged_context = build_merged_context(rag_context, web_context, news_context)

    # STEP 9: Generate LLM response
    answer = llm_generate(message, merged_context, session_id)

    sources = _sources_from_docs(rag_docs, limit=2)
    if not sources and web_context:
        # Provide web URLs as sources if KB had none.
        web_results = web_search_service.search(message, bank_name=bank_slug, max_results=2)
        for r in web_results[:2]:
            url = (r.get("href") or r.get("url") or "").strip()
            snippet = (r.get("body") or "").strip()
            if len(snippet) > 240:
                snippet = snippet[:240].rstrip() + "…"
            if url:
                sources.append({"url": url, "snippet": snippet})

    return {"response": answer, "sources": sources}


def chat(message: str) -> Dict[str, Any]:
    # Keep existing sync entrypoint for the FastAPI route.
    import asyncio

    return asyncio.run(get_response(session_id="api", message=message, bank_filter=None))

