from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.chat_service import chat as chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[dict]


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = chat_service(req.message)
    return ChatResponse(**result)

