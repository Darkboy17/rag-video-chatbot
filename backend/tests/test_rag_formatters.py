from unittest import TestCase

from app.schemas.video import VideoMetadata
from app.services.rag.formatters import format_video_stats


class RagFormatterTests(TestCase):
    def test_engagement_comparison_identifies_video_b_as_higher(self):
        videos = {
            "A": VideoMetadata(
                video_id="A",
                source_url="https://example.com/a",
                engagement_rate=1.9375,
            ),
            "B": VideoMetadata(
                video_id="B",
                source_url="https://example.com/b",
                engagement_rate=5.048,
            ),
        }

        stats = format_video_stats(videos)

        self.assertIn(
            "Engagement Comparison: Video B has higher engagement than Video A",
            stats,
        )

    def test_video_stats_formats_available_followers_explicitly(self):
        videos = {
            "B": VideoMetadata(
                video_id="B",
                source_url="https://example.com/b",
                creator="sayed.developer",
                follower_count=12500,
            ),
        }

        stats = format_video_stats(videos)

        self.assertIn("Creator: sayed.developer", stats)
        self.assertIn("Follower Count: 12,500", stats)
        self.assertNotIn("Follower Count: None", stats)

    def test_video_stats_formats_missing_followers_as_unavailable(self):
        videos = {
            "B": VideoMetadata(
                video_id="B",
                source_url="https://example.com/b",
                follower_count=None,
            ),
        }

        stats = format_video_stats(videos)

        self.assertIn("Follower Count: Unavailable from extraction", stats)
