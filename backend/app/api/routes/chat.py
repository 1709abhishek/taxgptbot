import uuid
from fastapi import APIRouter, Depends

from app.api.schemas import ChatRequest, ChatResponse
from app.llm.rag_pipeline import RAGPipeline

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return an answer with sources."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    pipeline = RAGPipeline()
    result = pipeline.process(request.message)

    return ChatResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        sources=result["sources"],
        graph_path=result["graph_path"],
        retrieval_debug=result["retrieval_debug"],
        conversation_id=conversation_id,
    )
