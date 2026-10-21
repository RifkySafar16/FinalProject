from fastapi import APIRouter

from src.backend.schemas import ChatRequest, ChatResponse
from src.rag.rag_engine import ask

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    return ask(request.question)
