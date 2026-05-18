from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from app.services.retrieval.vector_store import CHROMA_TELEMETRY_IMPL, VectorStoreService


class VectorStoreServiceTests(TestCase):
    @patch("app.services.retrieval.vector_store.get_embedding_model")
    @patch("app.services.retrieval.vector_store.get_settings")
    @patch("app.services.retrieval.vector_store.Chroma")
    def test_chroma_uses_noop_telemetry_client(
        self,
        mock_chroma,
        mock_get_settings,
        mock_get_embedding_model,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            chroma_collection="test_collection",
            chroma_dir="storage/chroma",
        )
        mock_get_embedding_model.return_value = Mock()

        VectorStoreService()

        client_settings = mock_chroma.call_args.kwargs["client_settings"]

        self.assertFalse(client_settings.anonymized_telemetry)
        self.assertEqual(
            client_settings.chroma_product_telemetry_impl,
            CHROMA_TELEMETRY_IMPL,
        )
        self.assertEqual(
            client_settings.chroma_telemetry_impl,
            CHROMA_TELEMETRY_IMPL,
        )

    @patch("app.services.retrieval.vector_store.get_embedding_model")
    @patch("app.services.retrieval.vector_store.get_settings")
    @patch("app.services.retrieval.vector_store.Chroma")
    def test_similarity_search_clamps_k_to_session_document_count(
        self,
        mock_chroma,
        mock_get_settings,
        mock_get_embedding_model,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            chroma_collection="test_collection",
            chroma_dir="storage/chroma",
        )
        mock_get_embedding_model.return_value = Mock()
        mock_store = Mock()
        mock_store.get.return_value = {"ids": ["chunk-1", "chunk-2"]}
        mock_store.similarity_search.return_value = []
        mock_chroma.return_value = mock_store

        service = VectorStoreService()
        service.similarity_search(query="question", session_id="session-1", k=6)

        mock_store.similarity_search.assert_called_once_with(
            query="question",
            k=2,
            filter={"session_id": "session-1"},
        )

    @patch("app.services.retrieval.vector_store.get_embedding_model")
    @patch("app.services.retrieval.vector_store.get_settings")
    @patch("app.services.retrieval.vector_store.Chroma")
    def test_similarity_search_returns_empty_when_session_has_no_documents(
        self,
        mock_chroma,
        mock_get_settings,
        mock_get_embedding_model,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            chroma_collection="test_collection",
            chroma_dir="storage/chroma",
        )
        mock_get_embedding_model.return_value = Mock()
        mock_store = Mock()
        mock_store.get.return_value = {"ids": []}
        mock_chroma.return_value = mock_store

        service = VectorStoreService()
        result = service.similarity_search(
            query="question",
            session_id="session-1",
            k=6,
        )

        self.assertEqual(result, [])
        mock_store.similarity_search.assert_not_called()

    @patch("app.services.retrieval.vector_store.get_embedding_model")
    @patch("app.services.retrieval.vector_store.get_settings")
    @patch("app.services.retrieval.vector_store.Chroma")
    def test_get_opening_hook_documents_filters_session_documents(
        self,
        mock_chroma,
        mock_get_settings,
        mock_get_embedding_model,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            chroma_collection="test_collection",
            chroma_dir="storage/chroma",
        )
        mock_get_embedding_model.return_value = Mock()
        mock_store = Mock()
        mock_store.get.return_value = {
            "documents": ["opening text", "normal text"],
            "metadatas": [
                {"chunk_id": "A-hook-0-5", "content_type": "opening_hook"},
                {"chunk_id": "A-1", "content_type": "transcript_chunk"},
            ],
        }
        mock_chroma.return_value = mock_store

        service = VectorStoreService()
        documents = service.get_opening_hook_documents("session-1")

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].page_content, "opening text")
        self.assertEqual(documents[0].metadata["chunk_id"], "A-hook-0-5")
