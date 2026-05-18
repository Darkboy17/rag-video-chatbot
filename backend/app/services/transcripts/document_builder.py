from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.schemas.video import VideoMetadata


class TranscriptDocumentBuilder:
    """
    Converts transcript entries into vector-store-ready LangChain documents.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def build(
        self,
        session_id: str,
        video: VideoMetadata,
        transcript_entries: List[dict],
    ) -> List[Document]:
        transcript_text = self._join_transcript(transcript_entries)
        chunks = self.splitter.split_text(transcript_text)
        documents = self._build_opening_hook_documents(
            session_id=session_id,
            video=video,
            transcript_entries=transcript_entries,
        )

        documents.extend(
            self._build_document(
                session_id=session_id,
                video=video,
                chunk=chunk,
                index=index,
            )
            for index, chunk in enumerate(chunks)
        )

        return documents

    def _join_transcript(self, transcript_entries: List[dict]) -> str:
        return "\n".join(
            self._format_transcript_entry(entry)
            for entry in transcript_entries
            if entry.get("text")
        )

    def _build_opening_hook_documents(
        self,
        session_id: str,
        video: VideoMetadata,
        transcript_entries: List[dict],
    ) -> List[Document]:
        opening_entries = [
            entry
            for entry in transcript_entries
            if self._overlaps_opening_window(entry, opening_seconds=5)
        ]

        if not opening_entries:
            return []

        chunk_id = f"{video.video_id}-hook-0-5"
        opening_text = "\n".join(
            self._format_transcript_entry(entry) for entry in opening_entries
        )

        return [
            Document(
                page_content=f"Opening hook (0-5 seconds)\n{opening_text}",
                metadata={
                    "session_id": session_id,
                    "video_id": video.video_id,
                    "chunk_id": chunk_id,
                    "source_url": video.source_url,
                    "title": video.title or "",
                    "creator": video.creator or "",
                    "content_type": "opening_hook",
                    "start_seconds": 0,
                    "end_seconds": 5,
                },
            )
        ]

    def _build_document(
        self,
        session_id: str,
        video: VideoMetadata,
        chunk: str,
        index: int,
    ) -> Document:
        chunk_id = f"{video.video_id}-{index + 1}"

        return Document(
            page_content=chunk,
            metadata={
                "session_id": session_id,
                "video_id": video.video_id,
                "chunk_id": chunk_id,
                "source_url": video.source_url,
                "title": video.title or "",
                "creator": video.creator or "",
                "content_type": "transcript_chunk",
            },
        )

    def _format_transcript_entry(self, entry: dict) -> str:
        text = entry.get("text", "").strip()
        start = self._safe_float(entry.get("start"))
        duration = self._safe_float(entry.get("duration"))

        if start is None:
            return text

        if duration is None:
            return f"[{start:.2f}s] {text}"

        end = start + duration
        return f"[{start:.2f}s-{end:.2f}s] {text}"

    def _overlaps_opening_window(self, entry: dict, opening_seconds: int) -> bool:
        start = self._safe_float(entry.get("start"))
        if start is None:
            return False

        duration = self._safe_float(entry.get("duration"))
        end = start + duration if duration is not None else start

        return start < opening_seconds and end >= 0

    def _safe_float(self, value) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
