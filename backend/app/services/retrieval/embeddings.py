from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import get_settings


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Local embedding model.

    BAAI/bge-small-en-v1.5 is a good demo choice:
    - free
    - local
    - fast enough
    - no per-request embedding cost
    """

    settings = get_settings()

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )