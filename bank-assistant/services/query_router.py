from __future__ import annotations

from enum import Enum


class QueryType(Enum):
    PRODUCT_INFO = "product_info"
    LEADERSHIP = "leadership"
    NEWS_EVENTS = "news_events"
    FINANCIAL_DATA = "financial_data"
    BRANCH_ATM = "branch_atm"
    REGULATORY = "regulatory"
    COMPARISON = "comparison"
    GENERAL_BANKING = "general_banking"
    CURRENT_RATES = "current_rates"


class QueryRouter:
    LEADERSHIP_KEYWORDS = [
        "ceo",
        "president",
        "chairman",
        "cfo",
        "coo",
        "md",
        "managing director",
        "chief executive",
        "head of",
        "director",
        "board",
        "management team",
        "leadership",
        "founded by",
        "founder",
        "who runs",
        "who leads",
        "appointed",
        "resigned",
        "promoted",
    ]

    NEWS_KEYWORDS = [
        "latest",
        "recent",
        "news",
        "announcement",
        "launched",
        "new product",
        "update",
        "2024",
        "2025",
        "this year",
        "last month",
        "just",
        "today",
        "award",
        "partnership",
        "merger",
        "acquisition",
        "expansion",
        "press release",
    ]

    RATES_KEYWORDS = [
        "current rate",
        "today's rate",
        "profit rate",
        "interest rate",
        "sbp rate",
        "kibor",
        "policy rate",
        "markup rate",
        "today",
    ]

    def route(self, query: str) -> dict:
        query_lower = (query or "").lower()

        if any(kw in query_lower for kw in self.LEADERSHIP_KEYWORDS):
            return {
                "use_rag": True,
                "use_web_search": True,
                "use_news_search": False,
                "query_type": QueryType.LEADERSHIP,
                "reason": "Leadership query — searching web + RAG for current info",
            }

        if any(kw in query_lower for kw in self.NEWS_KEYWORDS):
            return {
                "use_rag": False,
                "use_web_search": True,
                "use_news_search": True,
                "query_type": QueryType.NEWS_EVENTS,
                "reason": "News/recent query — using live search only",
            }

        if any(kw in query_lower for kw in self.RATES_KEYWORDS):
            return {
                "use_rag": True,
                "use_web_search": True,
                "use_news_search": False,
                "query_type": QueryType.CURRENT_RATES,
                "reason": "Rate query — combining RAG + web for most current data",
            }

        return {
            "use_rag": True,
            "use_web_search": False,
            "use_news_search": False,
            "query_type": QueryType.PRODUCT_INFO,
            "reason": "Product/service query — using RAG knowledge base",
        }

