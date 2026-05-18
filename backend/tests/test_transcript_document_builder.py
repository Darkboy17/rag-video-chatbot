from unittest import TestCase

from app.schemas.video import VideoMetadata
from app.services.transcripts.document_builder import TranscriptDocumentBuilder


class TranscriptDocumentBuilderTests(TestCase):
    def test_builds_opening_hook_document_from_timestamped_entries(self):
        builder = TranscriptDocumentBuilder(chunk_size=500, chunk_overlap=0)
        video = VideoMetadata(
            video_id="A",
            source_url="https://example.com/video",
            title="Example Video",
        )

        documents = builder.build(
            session_id="session-1",
            video=video,
            transcript_entries=[
                {"text": "Start strong", "start": 0.0, "duration": 2.5},
                {"text": "Second beat", "start": 4.5, "duration": 1.0},
                {"text": "Later detail", "start": 7.0, "duration": 2.0},
            ],
        )

        opening_doc = documents[0]

        self.assertEqual(opening_doc.metadata["chunk_id"], "A-hook-0-5")
        self.assertEqual(opening_doc.metadata["content_type"], "opening_hook")
        self.assertIn("Opening hook (0-5 seconds)", opening_doc.page_content)
        self.assertIn("[0.00s-2.50s] Start strong", opening_doc.page_content)
        self.assertIn("[4.50s-5.50s] Second beat", opening_doc.page_content)
        self.assertNotIn("Later detail", opening_doc.page_content)

    def test_does_not_build_opening_hook_without_timestamps(self):
        builder = TranscriptDocumentBuilder(chunk_size=500, chunk_overlap=0)
        video = VideoMetadata(
            video_id="B",
            source_url="https://example.com/video",
        )

        documents = builder.build(
            session_id="session-1",
            video=video,
            transcript_entries=[
                {"text": "Untimed transcript"},
            ],
        )

        self.assertEqual(documents[0].metadata["content_type"], "transcript_chunk")
        self.assertEqual(documents[0].page_content, "Untimed transcript")
