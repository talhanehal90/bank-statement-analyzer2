from __future__ import annotations

"""
Live web search fallback using DuckDuckGo — no API key required.
Used when RAG vector store has insufficient context.
"""

import logging
from typing import Any, Dict, List, Optional

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(self) -> None:
        self.ddgs = DDGS()

    def search(
        self, query: str, bank_name: str | None = None, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        search_query = (
            f"{bank_name} Pakistan {query}" if bank_name else f"{query} Pakistan bank"
        )
        try:
            results = list(
                self.ddgs.text(
                    search_query,
                    region="pk-en",
                    safesearch="moderate",
                    timelimit="y",
                    max_results=max_results,
                )
            )
            logger.info("DuckDuckGo returned %s results for: %s", len(results), search_query)
            return results
        except Exception as e:
            logger.error("DuckDuckGo search failed: %s", e)
            return []

    def search_news(
        self, query: str, bank_name: str | None = None, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        search_query = f"{bank_name} Pakistan {query}" if bank_name else query
        try:
            results = list(
                self.ddgs.news(
                    search_query,
                    region="pk-en",
                    safesearch="moderate",
                    timelimit="m",
                    max_results=max_results,
                )
            )
            return results
        except Exception as e:
            logger.error("DuckDuckGo news search failed: %s", e)
            return []

    def format_results_as_context(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""
        context_parts: list[str] = []
        for r in results:
            title = r.get("title", "") or ""
            body = r.get("body", "") or ""
            href = r.get("href", "") or r.get("url", "") or ""
            date = r.get("date", "") or ""
            if date:
                context_parts.append(f"Source: {title}\nDate: {date}\nURL: {href}\nContent: {body}")
            else:
                context_parts.append(f"Source: {title}\nURL: {href}\nContent: {body}")
        return "\n\n---\n\n".join(context_parts)

