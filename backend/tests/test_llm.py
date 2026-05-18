from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.services.rag.llm import get_chat_model


class LlmTests(TestCase):
    @patch("app.services.rag.llm.ChatGroq")
    @patch("app.services.rag.llm.get_settings")
    def test_chat_model_ignores_proxy_environment_by_default(
        self,
        mock_get_settings,
        mock_chat_groq,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            groq_api_key="test-key",
            groq_model="test-model",
            groq_trust_env=False,
        )

        get_chat_model(streaming=True)

        kwargs = mock_chat_groq.call_args.kwargs

        self.assertFalse(kwargs["http_client"]._trust_env)
        self.assertFalse(kwargs["http_async_client"]._trust_env)

    @patch("app.services.rag.llm.ChatGroq")
    @patch("app.services.rag.llm.get_settings")
    def test_chat_model_can_trust_proxy_environment_when_configured(
        self,
        mock_get_settings,
        mock_chat_groq,
    ):
        mock_get_settings.return_value = SimpleNamespace(
            groq_api_key="test-key",
            groq_model="test-model",
            groq_trust_env=True,
        )

        get_chat_model(streaming=False)

        kwargs = mock_chat_groq.call_args.kwargs

        self.assertTrue(kwargs["http_client"]._trust_env)
        self.assertTrue(kwargs["http_async_client"]._trust_env)
