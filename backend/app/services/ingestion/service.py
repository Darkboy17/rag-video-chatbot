import logging
from typing import List
from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document

from app.core.config import get_settings
from app.schemas.video import AnalyzeVideosRequest, AnalyzeVideosResponse, VideoMetadata
from app.services.extractors.video_extractor import UnsupportedPlatformError, VideoExtractor
from app.services.ingestion.progress import IngestionProgress, ProgressCallback
from app.services.rag.memory_store import memory_store
from app.services.retrieval.vector_store import VectorStoreService
from app.services.transcripts.document_builder import TranscriptDocumentBuilder
from app.services.transcripts.service import TranscriptService, TranscriptUnavailableError
from app.utils.memory import get_process_rss_bytes, log_memory_usage
from app.utils.url_utils import detect_social_platform


logger = logging.getLogger(__name__)


class VideoIngestionError(RuntimeError):
    """Raised when one video cannot be fetched, transcribed, or indexed."""

    def __init__(self, video_id: str, url: str, reason: str):
        self.video_id = video_id
        self.url = url
        self.reason = reason
        super().__init__(f"Video {video_id} could not be analyzed: {reason}")


class IngestionService:
    """
    Coordinates:
    - metadata extraction
    - transcript extraction
    - chunking
    - vector storage
    - session memory storage
    """

    def __init__(self):
        self.settings = get_settings()
        self.video_extractor = VideoExtractor()
        self.transcript_service = TranscriptService()
        self.document_builder = TranscriptDocumentBuilder(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        self.vector_store = VectorStoreService()

    def ingest_two_videos(
        self,
        request: AnalyzeVideosRequest,
        on_progress: ProgressCallback | None = None,
    ) -> AnalyzeVideosResponse:
        session_id = request.session_id or str(uuid4())
        baseline_rss_bytes = get_process_rss_bytes()
        log_memory_usage(
            logger,
            session_id=session_id,
            stage="session_started",
            baseline_bytes=baseline_rss_bytes,
        )

        progress = IngestionProgress(session_id, on_progress)
        progress.emit("Created analysis session.")

        try:
            videos: List[VideoMetadata] = []
            documents: List[Document] = []

            video_inputs = [
                ("A", request.video_a_url),
                ("B", request.video_b_url),
            ]
            detected_inputs = [
                (video_id, url, detect_social_platform(url))
                for video_id, url in video_inputs
            ]

            for video_id, url, platform in detected_inputs:
                progress.emit(f"Video {video_id}: detected {platform} URL.")

                if platform == "unknown":
                    progress.emit(f"Video {video_id}: unsupported platform.")
                    raise VideoIngestionError(
                        video_id=video_id,
                        url=url,
                        reason=(
                            "Unsupported video URL. Use a YouTube, TikTok, "
                            "or Instagram URL."
                        ),
                    )

                try:
                    progress.emit(f"Video {video_id}: extracting {platform} metadata.")
                    metadata = self.video_extractor.extract_metadata(
                        url=url,
                        video_id=video_id,
                    )
                except UnsupportedPlatformError as exc:
                    progress.emit(f"Video {video_id}: unsupported platform.")
                    raise VideoIngestionError(
                        video_id=video_id,
                        url=url,
                        reason=str(exc),
                    ) from exc

                progress.emit(
                    f"Video {video_id}: metadata extracted for "
                    f"{metadata.title or 'untitled video'}."
                )

                try:
                    progress.emit(f"Video {video_id}: fetching {platform} transcript.")
                    transcript_entries = self.transcript_service.get_transcript(
                        url=url,
                        platform=platform,
                    )
                except TranscriptUnavailableError as exc:
                    progress.emit(f"Video {video_id}: transcript extraction failed.")
                    raise VideoIngestionError(
                        video_id=video_id,
                        url=url,
                        reason=str(exc),
                    ) from exc

                progress.emit(
                    f"Video {video_id}: transcript ready with "
                    f"{len(transcript_entries)} segment(s)."
                )

                progress.emit(f"Video {video_id}: chunking transcript.")
                video_documents = self.document_builder.build(
                    session_id=session_id,
                    video=metadata,
                    transcript_entries=transcript_entries,
                )

                progress.emit(
                    f"Video {video_id}: created {len(video_documents)} chunk(s)."
                )

                videos.append(metadata)
                documents.extend(video_documents)

                memory_store.save_video(session_id, metadata)
                progress.emit(f"Video {video_id}: saved metadata to session memory.")
                log_memory_usage(
                    logger,
                    session_id=session_id,
                    stage=f"video_{video_id}_processed",
                    baseline_bytes=baseline_rss_bytes,
                )

            progress.emit(
                f"Indexing {len(documents)} transcript chunk(s) in vector store."
            )
            self.vector_store.add_documents(documents)
            progress.emit("Vector index updated.")
            log_memory_usage(
                logger,
                session_id=session_id,
                stage="vector_indexed",
                baseline_bytes=baseline_rss_bytes,
            )

            response = AnalyzeVideosResponse(
                session_id=session_id,
                videos=videos,
                chunks_indexed=len(documents),
            )

            progress.emit("Analysis complete.")
            self._cleanup_downloads()

            log_memory_usage(
                logger,
                session_id=session_id,
                stage="session_completed",
                baseline_bytes=baseline_rss_bytes,
            )

            return response
        except Exception:
            log_memory_usage(
                logger,
                session_id=session_id,
                stage="session_failed",
                baseline_bytes=baseline_rss_bytes,
            )
            raise

    def _cleanup_downloads(self) -> None:
        download_dir = Path(self.settings.download_dir).resolve()

        if not download_dir.exists() or not download_dir.is_dir():
            return

        for path in download_dir.iterdir():
            if not path.is_file():
                continue

            try:
                path.unlink()
            except OSError:
                pass
