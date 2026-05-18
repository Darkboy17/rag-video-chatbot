from fastapi import APIRouter

from app.api.chat_routes import router as chat_router
from app.api.video_routes import router as video_router

# Top-level API router mounted by the FastAPI app. Every route included here is
# exposed under the shared /api prefix.
router = APIRouter(prefix="/api", tags=["Social Video RAG"])

# Register feature-specific route groups while keeping their implementations in
# separate modules.
router.include_router(video_router)
router.include_router(chat_router)


@router.get("/health")
def health_check():
    """
    Lightweight readiness endpoint for clients, deployment checks, and dev tools.
    """

    return {
        "status": "ok",
        "service": "social-video-rag-api",
    }
