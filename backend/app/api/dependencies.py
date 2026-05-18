from functools import lru_cache

from app.services.ingestion.service import IngestionService
from app.services.rag.service import RagService


@lru_cache
def get_ingestion_service() -> IngestionService:
    """
    Lazily initialize ingestion dependencies on the first analyze request.
    """

    return IngestionService()


@lru_cache
def get_rag_service() -> RagService:
    """
    Lazily initialize retrieval/chat dependencies on the first chat request.
    """

    return RagService()
