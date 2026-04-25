from __future__ import annotations

from typing import List

from .vector_store import RetrievedDoc


SYSTEM_PROMPT = """
You are BankBot — Pakistan's most knowledgeable AI banking assistant.
You have access to both a knowledge base of official bank data AND 
live web search results.

ANSWERING RULES:
1. ALWAYS answer — never say "I don't know" without trying all sources.
2. For leadership questions (CEO, Chairman, MD): use the provided 
   leadership data directly and answer confidently with the person's name.
3. For product/service questions: use the knowledge base context.
4. For news/recent events: use the web search results, mention the date.
5. For rates: state the rate from context AND advise to verify on 
   official bank website as rates change frequently.
6. ALWAYS name the specific bank in your answer.
7. If info comes from web search, say "According to recent web sources..."
8. If info comes from knowledge base, say "Based on official bank data..."
9. Format with bullet points for lists of features.
10. End every response with the bank's official website and helpline 
    if you have it.
11. Support Urdu/Roman Urdu — detect language and respond accordingly.
12. NEVER fabricate names, rates, or figures not present in context.

TONE: Professional, helpful, concise. Like a knowledgeable bank officer.
"""


def format_context(docs: List[RetrievedDoc]) -> str:
    if not docs:
        return "(no documents retrieved)"

    chunks: list[str] = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source") or d.metadata.get("url") or d.id
        chunks.append(f"[{i}] source: {src}\n{d.text}")
    return "\n\n".join(chunks)


def build_prompt(question: str, docs: List[RetrievedDoc]) -> str:
    context = format_context(docs)
    return (
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{question}\n\n"
        "Answer in natural language. Keep it short. When relevant, cite sources like [1], [2]."
    )

