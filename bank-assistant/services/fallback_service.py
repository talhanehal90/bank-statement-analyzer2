from __future__ import annotations

import json
from pathlib import Path


class FallbackService:
    """
    Fallback knowledge service — checks hardcoded JSON before giving up.
    """

    def __init__(self) -> None:
        path = Path("data/fallback_knowledge.json")
        with path.open(encoding="utf-8") as f:
            self.knowledge = json.load(f)

    def get_bank_leadership(self, bank_slug: str) -> dict | None:
        return self.knowledge.get("bank_leadership", {}).get(bank_slug)

    def answer_leadership_query(self, query: str, bank_slug: str) -> str | None:
        info = self.get_bank_leadership(bank_slug)
        if not info:
            return None

        query_lower = (query or "").lower()
        bank_title = bank_slug.replace("_", " ").title()

        if any(kw in query_lower for kw in ["ceo", "chief executive", "head", "president"]):
            return (
                f"The CEO/President of {bank_title} is {info.get('ceo', 'not available')} "
                f"({info.get('designation', '')})."
            )
        if "chairman" in query_lower:
            return f"The Chairman is {info.get('chairman', 'information not available')}."
        if "founded" in query_lower or "established" in query_lower:
            return f"Founded in {info.get('founded', 'year not available')}."
        if "headquarter" in query_lower or "hq" in query_lower:
            return f"Headquartered in {info.get('headquarters', 'not available')}."

        return (
            f"Leadership of {bank_title}:\n"
            f"• CEO/President: {info.get('ceo', 'N/A')}\n"
            f"• Chairman: {info.get('chairman', 'N/A')}\n"
            f"• Founded: {info.get('founded', 'N/A')}\n"
            f"• HQ: {info.get('headquarters', 'N/A')}"
        )

    def answer_sbp_policy_rate(self) -> str | None:
        sbp = self.knowledge.get("sbp_info", {})
        if not sbp:
            return None
        rate = sbp.get("policy_rate_as_of_2024")
        website = sbp.get("website")
        if not rate:
            return None
        if website:
            return f"SBP policy rate (fallback): {rate}. Please verify the latest on SBP: {website}"
        return f"SBP policy rate (fallback): {rate}. Please verify the latest on SBP website."

