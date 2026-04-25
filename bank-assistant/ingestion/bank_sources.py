from __future__ import annotations

from typing import Any, Dict, List, TypedDict

import chromadb

from rag.vector_store import COLLECTION_NAME, PERSIST_DIR, add_documents

from .chunker import chunk_text
from .scraper import fetch_visible_text


class BankEntry(TypedDict):
    name: str
    website: str
    urls: List[str]


LEADERSHIP_PATHS: list[str] = [
    "/about-us/management-team",
    "/about-us/board-of-directors",
    "/about-us/leadership",
    "/about-us/executive-team",
    "/investor-relations/corporate-governance",
    "/about/our-team",
    "/management",
    "/governance",
]

NEWS_PATHS: list[str] = [
    "/media-center",
    "/news",
    "/press-releases",
    "/latest-news",
    "/newsroom",
    "/investor-relations/news",
    "/media/press-releases",
    "/updates",
]

FINANCIAL_PATHS: list[str] = [
    "/investor-relations",
    "/investor-relations/financial-highlights",
    "/investor-relations/annual-reports",
    "/financial-results",
    "/quarterly-results",
    "/investor-relations/financial-statements",
]

CSR_PATHS: list[str] = [
    "/csr",
    "/corporate-social-responsibility",
    "/awards-recognition",
    "/sustainability",
]

CAREERS_PATHS: list[str] = [
    "/careers",
    "/about-us/our-story",
    "/about-us/milestones",
    "/history",
]


def _join(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _wikipedia_urls(bank_name: str) -> list[str]:
    # Wikipedia uses underscores for spaces.
    slug = bank_name.strip().replace(" ", "_")
    return [
        f"https://en.wikipedia.org/wiki/{slug}",
        f"https://en.wikipedia.org/wiki/{slug}_Pakistan",
    ]


def _expand_urls(website: str, seed_urls: list[str]) -> list[str]:
    website = website.rstrip("/")
    paths = LEADERSHIP_PATHS + NEWS_PATHS + FINANCIAL_PATHS + CSR_PATHS + CAREERS_PATHS
    guessed = [_join(website, p) for p in paths]
    # De-dupe, keep order
    seen: set[str] = set()
    out: list[str] = []
    for u in seed_urls + guessed:
        u = (u or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


# NOTE: This list is intentionally broad (40+). Any blocked/404 pages are skipped gracefully by the scraper.
BANKS: dict[str, dict[str, Any]] = {
    "hbl": {
        "name": "HBL",
        "website": "https://www.hbl.com",
        "seed_urls": [
            "https://www.hbl.com/",
            "https://www.hbl.com/personal/",
            "https://www.hbl.com/personal/personal/loans/hbl-personal-loan",
        ],
    },
    "ubl": {
        "name": "United Bank Limited",
        "website": "https://www.ubldigital.com",
        "seed_urls": [
            "https://www.ubldigital.com/",
            "https://www.ubldigital.com/Deposits/",
            "https://www.ubldigital.com/Loans/Consumer-Loans",
        ],
    },
    "mcb_bank": {
        "name": "MCB Bank",
        "website": "https://www.mcb.com.pk",
        "seed_urls": [
            "https://www.mcb.com.pk/",
            "https://www.mcb.com.pk/personal/",
            "https://www.mcb.com.pk/personal/consumer-loans",
        ],
    },
    "meezan_bank": {
        "name": "Meezan Bank",
        "website": "https://www.meezanbank.com",
        "seed_urls": [
            "https://www.meezanbank.com/",
            "https://www.meezanbank.com/bank-accounts/",
            "https://www.meezanbank.com/consumer-ease/",
            "https://www.meezanbank.com/car-ijarah/",
            "https://www.meezanbank.com/home-finance/",
            "https://www.meezanbank.com/profit-rates/",
        ],
    },
    "nbp": {
        "name": "National Bank of Pakistan",
        "website": "https://www.nbp.com.pk",
        "seed_urls": [
            "https://www.nbp.com.pk/",
            "https://www.nbp.com.pk/PersonalBanking.asp",
            "https://www.nbp.com.pk/Saibaan/main.aspx",
            "https://www.nbp.com.pk/advancesalary/main.aspx",
        ],
    },
    "bank_alfalah": {"name": "Bank Alfalah", "website": "https://www.bankalfalah.com", "seed_urls": ["https://www.bankalfalah.com/"]},
    "allied_bank": {"name": "Allied Bank", "website": "https://www.abl.com", "seed_urls": ["https://www.abl.com/"]},
    "askari_bank": {"name": "Askari Bank", "website": "https://askaribank.com.pk", "seed_urls": ["https://askaribank.com.pk/"]},
    "bank_of_punjab": {"name": "Bank of Punjab", "website": "https://www.bop.com.pk", "seed_urls": ["https://www.bop.com.pk/"]},
    "faysal_bank": {"name": "Faysal Bank", "website": "https://www.faysalbank.com", "seed_urls": ["https://www.faysalbank.com/"]},
    "habib_metro": {"name": "Habib Metropolitan Bank", "website": "https://www.habibmetro.com", "seed_urls": ["https://www.habibmetro.com/"]},
    "bank_islami": {"name": "BankIslami", "website": "https://www.bankislami.com.pk", "seed_urls": ["https://www.bankislami.com.pk/"]},
    "al_baraka": {"name": "Al Baraka Bank Pakistan", "website": "https://www.albaraka.com.pk", "seed_urls": ["https://www.albaraka.com.pk/"]},
    "js_bank": {"name": "JS Bank", "website": "https://www.jsbl.com", "seed_urls": ["https://www.jsbl.com/"]},
    "soneri_bank": {"name": "Soneri Bank", "website": "https://www.soneribank.com", "seed_urls": ["https://www.soneribank.com/"]},
    "samba_bank": {"name": "Samba Bank", "website": "https://www.samba.com.pk", "seed_urls": ["https://www.samba.com.pk/"]},
    "summit_bank": {"name": "Summit Bank", "website": "https://www.summitbank.com.pk", "seed_urls": ["https://www.summitbank.com.pk/"]},
    "silkbank": {"name": "Silkbank", "website": "https://www.silkbank.com.pk", "seed_urls": ["https://www.silkbank.com.pk/"]},
    "standard_chartered": {"name": "Standard Chartered Pakistan", "website": "https://www.sc.com/pk", "seed_urls": ["https://www.sc.com/pk/"]},
    "citi_pakistan": {"name": "Citibank Pakistan", "website": "https://www.citigroup.com", "seed_urls": ["https://www.citigroup.com/"]},
    "hsbc": {"name": "HSBC", "website": "https://www.hsbc.com", "seed_urls": ["https://www.hsbc.com/"]},
    "deutsche_bank": {"name": "Deutsche Bank", "website": "https://www.db.com", "seed_urls": ["https://www.db.com/"]},
    "habib_bank_ag_zurich": {"name": "Habib Bank AG Zurich", "website": "https://www.habibbank.com", "seed_urls": ["https://www.habibbank.com/"]},
    "mcb_islamic": {"name": "MCB Islamic Bank", "website": "https://www.mcbislamicbank.com", "seed_urls": ["https://www.mcbislamicbank.com/"]},
    "ubl_ameen": {"name": "UBL Ameen", "website": "https://www.ubldigital.com", "seed_urls": ["https://www.ubldigital.com/Banking/UBLAmeen/AboutUs"]},
    "hbl_konnect": {"name": "HBL Konnect", "website": "https://www.hbl.com", "seed_urls": ["https://www.hbl.com/konnect"]},
    # Microfinance / branchless / fintech (to broaden coverage)
    "khushhali_microfinance": {"name": "Khushhali Microfinance Bank", "website": "https://www.khushhalibank.com.pk", "seed_urls": ["https://www.khushhalibank.com.pk/"]},
    "mobilink_microfinance": {"name": "Mobilink Microfinance Bank", "website": "https://www.mobilinkbank.com", "seed_urls": ["https://www.mobilinkbank.com/"]},
    "telenor_microfinance": {"name": "Telenor Microfinance Bank", "website": "https://www.telenorbank.pk", "seed_urls": ["https://www.telenorbank.pk/"]},
    "pak_oman_microfinance": {"name": "Pak Oman Microfinance Bank", "website": "https://www.pomb.com.pk", "seed_urls": ["https://www.pomb.com.pk/"]},
    "first_microfinance": {"name": "First MicroFinanceBank", "website": "https://www.fmfb.com.pk", "seed_urls": ["https://www.fmfb.com.pk/"]},
    "finja": {"name": "Finja", "website": "https://finja.pk", "seed_urls": ["https://finja.pk/"]},
    "naya_pay": {"name": "NayaPay", "website": "https://www.nayapay.com", "seed_urls": ["https://www.nayapay.com/"]},
    "sada_pay": {"name": "SadaPay", "website": "https://sadapay.pk", "seed_urls": ["https://sadapay.pk/"]},
    # Add more domestic banks to push beyond 40
    "bank_al_habib": {"name": "Bank AL Habib", "website": "https://www.bankalhabib.com", "seed_urls": ["https://www.bankalhabib.com/"]},
    "bank_of_khyber": {"name": "Bank of Khyber", "website": "https://www.bok.com.pk", "seed_urls": ["https://www.bok.com.pk/"]},
    "nib_bank_legacy": {"name": "NIB Bank", "website": "https://en.wikipedia.org/wiki/NIB_Bank", "seed_urls": ["https://en.wikipedia.org/wiki/NIB_Bank"]},
    "dubai_islamic_bank": {"name": "Dubai Islamic Bank Pakistan", "website": "https://www.dibpak.com", "seed_urls": ["https://www.dibpak.com/"]},
    "the_bank_of_khyber": {"name": "The Bank of Khyber", "website": "https://www.bok.com.pk", "seed_urls": ["https://www.bok.com.pk/"]},
    "zarai_taraqiati_bank": {"name": "Zarai Taraqiati Bank Limited", "website": "https://www.ztbl.com.pk", "seed_urls": ["https://www.ztbl.com.pk/"]},
    "industrial_development_bank": {"name": "Industrial Development Bank of Pakistan", "website": "https://en.wikipedia.org/wiki/Industrial_Development_Bank_of_Pakistan", "seed_urls": ["https://en.wikipedia.org/wiki/Industrial_Development_Bank_of_Pakistan"]},
}


def build_bank_entries() -> dict[str, BankEntry]:
    out: dict[str, BankEntry] = {}
    for slug, b in BANKS.items():
        name = b["name"]
        website = b["website"]
        seed_urls: list[str] = list(b.get("seed_urls") or [])
        urls = _expand_urls(website, seed_urls)
        urls += [u for u in _wikipedia_urls(name) if u not in urls]
        out[slug] = {"name": name, "website": website, "urls": urls}
    return out


def ingest_all_banks() -> dict[str, Any]:
    """
    Scrape configured bank pages, chunk visible text, and store into ChromaDB
    collection ``banking_kb`` (persistent store at ./chroma_db).

    Any individual URL that 404s/blocks will be skipped gracefully.
    """
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    banks = build_bank_entries()

    all_texts: list[str] = []
    all_metas: list[dict[str, Any]] = []
    all_ids: list[str] = []

    for bank_slug, bank in banks.items():
        bank_name = bank["name"]
        for url in bank["urls"]:
            raw = fetch_visible_text(url)
            if not raw:
                continue
            pieces = chunk_text(raw, chunk_size=500, overlap=100)
            for i, chunk in enumerate(pieces):
                cid = f"{bank_slug}|{i}|{hash(url) & 0xFFFFFFFF:x}"
                all_ids.append(cid)
                all_texts.append(chunk)
                all_metas.append(
                    {
                        "bank_name": bank_slug,
                        "bank_display": bank_name,
                        "source": url,
                    }
                )

    added = add_documents(all_texts, metadatas=all_metas, ids=all_ids)
    return {"chunks_indexed": added, "banks": [banks[k]["name"] for k in banks.keys()]}
