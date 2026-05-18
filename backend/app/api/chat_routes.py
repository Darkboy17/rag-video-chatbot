from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_rag_service
from app.schemas.chat import ChatStreamRequest

router = APIRouter(tags=["RAG chat"])


@router.post("/chat/stream")
async def stream_chat(payload: ChatStreamRequest):
    """
    Stream RAG answer tokens and source citations as Server-Sent Events.
    """

    return StreamingResponse(
        get_rag_service().stream_chat(
            session_id=payload.session_id,
            message=payload.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
