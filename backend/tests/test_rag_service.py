from unittest import TestCase

from app.schemas.video import VideoMetadata
from app.services.rag.service import RagService


class RagServiceTests(TestCase):
    def test_answers_creator_and_follower_metadata_without_llm(self):
        service = RagService.__new__(RagService)
        videos = {
            "B": VideoMetadata(
                video_id="B",
                source_url="https://example.com/b",
                creator="sayed.developer",
                follower_count=12500,
            )
        }

        answer = service._answer_direct_metadata_question(
            videos=videos,
            message="Who's the creator of Video B and what's their follower count?",
        )

        self.assertEqual(
            answer,
            "The creator of Video B is sayed.developer, and their follower count is 12,500.",
        )

    def test_does_not_treat_generic_who_question_as_metadata_shortcut(self):
        service = RagService.__new__(RagService)
        videos = {
            "A": VideoMetadata(
                video_id="A",
                source_url="https://example.com/a",
                creator="creator.a",
            )
        }

        answer = service._answer_direct_metadata_question(
            videos=videos,
            message="Who performed better, Video A or Video B?",
        )

        self.assertIsNone(answer)
