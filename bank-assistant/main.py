from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes.chat import router as chat_router
from ingestion.bank_sources import ingest_all_banks

load_dotenv()

app = FastAPI(title="Minimal FastAPI Backend", version="0.0.1")

app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": os.getenv("APP_ENV", "unknown")}


@app.post("/ingest")
def ingest() -> dict[str, object]:
    """
    Trigger a simple ingestion run that scrapes configured bank pages,
    chunks the text, and stores it in the persistent ChromaDB directory.
    """
    return ingest_all_banks()
