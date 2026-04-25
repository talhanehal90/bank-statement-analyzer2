from __future__ import annotations

import re
from typing import Final

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_visible_text(url: str, timeout: int = 30) -> str:
    """
    Fetch a page and return visible text (no scripts/styles), whitespace-normalized.
    Returns empty string on network/HTTP/parsing failures.
    """
    url = (url or "").strip()
    if not url:
        return ""

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code >= 400:
            return ""
        html = resp.text or ""
    except requests.RequestException:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text
