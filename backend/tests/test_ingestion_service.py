from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from app.schemas.video import AnalyzeVideosRequest, VideoMetadata
from app.services.ingestion.service import IngestionService, VideoIngestionError


class IngestionServiceTests(TestCase):
    def test_cleans_download_files_after_analysis_complete(self):
        with TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir)
            downloaded_video = download_dir / "source.mp4"
            downloaded_audio = download_dir / "source.mp3"
            nested_dir = download_dir / "nested"
            nested_dir.mkdir()
            nested_file = nested_dir / "keep.mp4"

            downloaded_video.write_text("video")
            downloaded_audio.write_text("audio")
            nested_file.write_text("nested")

            service = self._build_service(download_dir)
            progress_messages: list[str] = []

            response = service.ingest_two_videos(
                AnalyzeVideosRequest(
                    video_a_url="https://www.youtube.com/shorts/AAA",
                    video_b_url="https://www.youtube.com/shorts/BBB",
                ),
                on_progress=progress_messages.append,
            )

            self.assertEqual(response.chunks_indexed, 2)
            self.assertIn("Analysis complete.", progress_messages)
            self.assertFalse(downloaded_video.exists())
            self.assertFalse(downloaded_audio.exists())
            self.assertTrue(nested_file.exists())

    def test_preserves_download_files_when_analysis_fails_before_complete(self):
        with TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir)
            downloaded_video = download_dir / "source.mp4"
            downloaded_video.write_text("video")

            service = self._build_service(download_dir)
            service.transcript_service.get_transcript.side_effect = (
                RuntimeError("transcript broke")
            )

            with self.assertRaises(RuntimeError):
                service.ingest_two_videos(
                    AnalyzeVideosRequest(
                        video_a_url="https://www.youtube.com/shorts/AAA",
                        video_b_url="https://www.youtube.com/shorts/BBB",
                    )
                )

            self.assertTrue(downloaded_video.exists())

    def _build_service(self, download_dir: Path) -> IngestionService:
        service = IngestionService.__new__(IngestionService)
        service.settings = SimpleNamespace(download_dir=str(download_dir))

        service.video_extractor = Mock()
        service.video_extractor.extract_metadata.side_effect = [
            VideoMetadata(
                video_id="A",
                source_url="https://www.youtube.com/shorts/AAA",
                platform_id="AAA",
                title="Video A",
            ),
            VideoMetadata(
                video_id="B",
                source_url="https://www.youtube.com/shorts/BBB",
                platform_id="BBB",
                title="Video B",
            ),
        ]

        service.transcript_service = Mock()
        service.transcript_service.get_transcript.return_value = [
            {"text": "hello", "start": 0}
        ]

        service.document_builder = Mock()
        service.document_builder.build.side_effect = [["doc-a"], ["doc-b"]]

        service.vector_store = Mock()

        return service
