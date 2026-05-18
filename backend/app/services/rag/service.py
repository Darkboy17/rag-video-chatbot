import asyncio
import re
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import get_settings
from app.services.rag.formatters import (
    build_system_prompt,
    format_context,
    format_sources,
    format_video_stats,
)
from app.services.rag.llm import get_chat_model
from app.services.rag.memory_store import memory_store
from app.services.retrieval.vector_store import VectorStoreService
from app.utils.sse import sse_event


class RagService:
    """
    RAG service with:
    - retrieval
    - metadata-aware context
    - chat memory
    - streaming
    - citations
    """

    def __init__(self):
        self.settings = get_settings()
        self.vector_store = VectorStoreService()
        self.llm = get_chat_model(streaming=True)

    async def stream_chat(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[str, None]:
        try:
            videos = memory_store.get_videos(session_id)

            if not videos:
                yield sse_event(
                    "error",
                    {
                        "message": "No videos found for this session. Analyze two videos first."
                    },
                )
                return

            metadata_answer = self._answer_direct_metadata_question(
                videos=videos,
                message=message,
            )
            if metadata_answer:
                yield sse_event("token", {"text": metadata_answer})
                memory_store.append_message(
                    session_id, HumanMessage(content=message))
                memory_store.append_message(
                    session_id, AIMessage(content=metadata_answer))
                yield sse_event("sources", {"sources": []})
                yield sse_event("done", {"message": "completed"})
                return

            retrieved_docs = self.vector_store.similarity_search(
                query=message,
                session_id=session_id,
                k=self.settings.retrieval_k,
            )
            if self._asks_about_opening_hook(message):
                opening_docs = self.vector_store.get_opening_hook_documents(session_id)
                retrieved_docs = self._merge_documents(opening_docs, retrieved_docs)

            context = format_context(retrieved_docs)
            video_stats = format_video_stats(videos)
            sources = format_sources(retrieved_docs)

            history = memory_store.get_messages(session_id)

            system_prompt = build_system_prompt(
                video_stats=video_stats,
                context=context,
            )

            messages = [
                SystemMessage(content=system_prompt),
                *history[-8:],
                HumanMessage(content=message),
            ]

            full_answer = ""

            async for chunk in self.llm.astream(messages):
                token = chunk.content or ""

                if token:
                    full_answer += token
                    yield sse_event("token", {"text": token})
                    await asyncio.sleep(0)

            memory_store.append_message(
                session_id, HumanMessage(content=message))
            memory_store.append_message(
                session_id, AIMessage(content=full_answer))

            yield sse_event("sources", {"sources": sources})
            yield sse_event("done", {"message": "completed"})

        except Exception as exc:
            yield sse_event(
                "error",
                {
                    "message": str(exc),
                },
            )

    def _asks_about_opening_hook(self, message: str) -> bool:
        normalized = message.lower()
        return any(
            phrase in normalized
            for phrase in (
                "hook",
                "first 5",
                "first five",
                "opening",
                "0-5",
                "0 to 5",
                "first seconds",
            )
        )

    def _merge_documents(self, priority_docs, retrieved_docs):
        merged = []
        seen_chunk_ids = set()

        for doc in [*priority_docs, *retrieved_docs]:
            chunk_id = doc.metadata.get("chunk_id") or id(doc)
            if chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(chunk_id)
            merged.append(doc)

        return merged

    def _answer_direct_metadata_question(self, videos, message: str) -> str | None:
        normalized = message.lower()
        asks_creator = "creator" in normalized
        asks_followers = "follower" in normalized or "followers" in normalized

        if not asks_creator and not asks_followers:
            return None

        video_id = self._requested_video_id(normalized)
        if not video_id:
            return None

        video = videos.get(video_id)
        if not video:
            return None

        parts = []

        if asks_creator:
            creator = video.creator or video.creator_id
            if creator:
                parts.append(f"the creator of Video {video_id} is {creator}")
            else:
                parts.append(
                    f"the creator of Video {video_id} is unavailable from extraction"
                )

        if asks_followers:
            if video.follower_count is not None:
                parts.append(
                    f"their follower count is {video.follower_count:,}"
                )
            else:
                parts.append(
                    "their follower count is unavailable from extraction"
                )

        if not parts:
            return None

        first_part = parts[0][0].upper() + parts[0][1:]
        return f"{first_part}{_join_sentence_parts(parts[1:])}."

    def _requested_video_id(self, normalized_message: str) -> str | None:
        match = re.search(r"\bvideo\s*([ab])\b", normalized_message)
        if match:
            return match.group(1).upper()

        match = re.search(r"\b([ab])\b", normalized_message)
        if match:
            return match.group(1).upper()

        return None


def _join_sentence_parts(parts: list[str]) -> str:
    if not parts:
        return ""

    return ", and " + ", and ".join(parts)
