import httpx
from langchain_groq import ChatGroq

from app.core.config import get_settings


def get_chat_model(streaming: bool = True) -> ChatGroq:
    """
    Factory for the Groq chat model.

    Using a factory avoids global side effects and keeps testing easier.
    """

    settings = get_settings()

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.2,
        streaming=streaming,
        http_client=httpx.Client(trust_env=settings.groq_trust_env), 
        http_async_client=httpx.AsyncClient(trust_env=settings.groq_trust_env),
    )
