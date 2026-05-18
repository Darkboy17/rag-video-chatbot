from typing import List
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import get_settings
from app.services.retrieval.embeddings import get_embedding_model

CHROMA_TELEMETRY_IMPL = "app.services.retrieval.chroma_telemetry.NoOpTelemetryClient"


class VectorStoreService:
    """
    Handles vector DB operations.

    Currently using:
    - Chroma for local demo.

    Production swap:
    - Qdrant, Pinecone, Weaviate, or pgvector.
    """

    def __init__(self):
        settings = get_settings()

        self.store = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=get_embedding_model(),
            persist_directory=settings.chroma_dir,
            client_settings=ChromaSettings(
                anonymized_telemetry=False,
                chroma_product_telemetry_impl=CHROMA_TELEMETRY_IMPL,
                chroma_telemetry_impl=CHROMA_TELEMETRY_IMPL,
            ),
        )

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        self.store.add_documents(documents)

    def similarity_search(
        self,
        query: str,
        session_id: str,
        k: int,
    ) -> List[Document]:
        """
        Search only within the current user's session.

        This prevents chunks from previous demos/users leaking into the answer.
        """

        filter_by_session = {"session_id": session_id}
        available_results = self._count_session_documents(filter_by_session)
        if available_results <= 0:
            return []

        return self.store.similarity_search(
            query=query,
            k=min(k, available_results),
            filter=filter_by_session,
        )

    def get_opening_hook_documents(self, session_id: str) -> List[Document]:
        session_documents = self.store.get(
            where={"session_id": session_id},
            include=["metadatas", "documents"],
        )

        documents: List[Document] = []
        for page_content, metadata in zip(
            session_documents.get("documents", []),
            session_documents.get("metadatas", []),
        ):
            metadata = metadata or {}
            if metadata.get("content_type") != "opening_hook":
                continue

            documents.append(
                Document(
                    page_content=page_content,
                    metadata=metadata,
                )
            )

        return documents

    def _count_session_documents(self, filter_by_session: dict[str, str]) -> int:
        session_documents = self.store.get(
            where=filter_by_session,
            include=["metadatas"],
        )

        return len(session_documents.get("ids", []))
