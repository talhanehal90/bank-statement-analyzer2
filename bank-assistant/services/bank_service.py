from __future__ import annotations


BANK_ALIASES: dict[str, str] = {
    "meezan": "meezan_bank",
    "meezan bank": "meezan_bank",
    "hbl": "hbl",
    "habib bank": "hbl",
    "habib bank limited": "hbl",
    "mcb": "mcb_bank",
    "muslim commercial": "mcb_bank",
    "ubl": "ubl",
    "united bank": "ubl",
    "alfalah": "bank_alfalah",
    "bank alfalah": "bank_alfalah",
    "nbp": "nbp",
    "national bank": "nbp",
    "abl": "allied_bank",
    "allied bank": "allied_bank",
    "askari": "askari_bank",
    "bop": "bank_of_punjab",
    "bank of punjab": "bank_of_punjab",
    "faysal": "faysal_bank",
    "bankislami": "bank_islami",
    "bank islami": "bank_islami",
    "easypaisa": "telenor_microfinance",
    "jazzcash": "mobilink_microfinance",
    "nayapay": "naya_pay",
    "sadapay": "sada_pay",
    "standard chartered": "standard_chartered",
    "scb": "standard_chartered",
    "habib metro": "habib_metro",
    "habib metropolitan": "habib_metro",
    "soneri": "soneri_bank",
    "al baraka": "al_baraka",
    "albaraka": "al_baraka",
    "dib": "dubai_islamic_bank",
    "dubai islamic": "dubai_islamic_bank",
}


def detect_bank_from_message(message: str) -> str | None:
    """
    Scans message text for any bank name or alias.
    Returns the bank_slug if found, None otherwise.
    """
    msg = (message or "").lower()
    for alias in sorted(BANK_ALIASES.keys(), key=len, reverse=True):
        if alias in msg:
            return BANK_ALIASES[alias]
    return None

