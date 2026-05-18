from unittest import TestCase
from unittest.mock import Mock

from app.schemas.video import VideoMetadata
from app.services.extractors.instagram_extractor import InstagramVideoExtractor


class InstagramVideoExtractorTests(TestCase):
    def setUp(self):
        self.extractor = InstagramVideoExtractor.__new__(InstagramVideoExtractor)

    def test_fetches_followers_even_when_direct_views_exist(self):
        self.extractor._fetch_counts_from_profile = Mock(
            return_value={
                "follower_count": 12345,
                "views": None,
                "likes": None,
                "comments": None,
            }
        )
        metadata = VideoMetadata(
            video_id="A",
            source_url="https://www.instagram.com/creator/reel/ABC123/",
            platform_id="ABC123",
            creator="creator",
            views=1000,
            likes=90,
            comments=10,
            raw={},
        )

        result = self.extractor._postprocess_metadata(
            metadata=metadata,
            info={"id": "ABC123", "uploader": "creator"},
            url="https://www.instagram.com/creator/reel/ABC123/",
        )

        self.assertEqual(result.views, 1000)
        self.assertEqual(result.follower_count, 12345)
        self.extractor._fetch_counts_from_profile.assert_called_once_with(
            username="creator",
            shortcode="ABC123",
        )

    def test_uses_url_username_when_info_omits_creator_fields(self):
        self.extractor._fetch_counts_from_profile = Mock(
            return_value={
                "follower_count": 12345,
                "views": 2000,
                "likes": 100,
                "comments": 20,
            }
        )
        metadata = VideoMetadata(
            video_id="A",
            source_url="https://www.instagram.com/creator/reel/ABC123/",
            platform_id="ABC123",
            raw={},
        )

        result = self.extractor._postprocess_metadata(
            metadata=metadata,
            info={"id": "ABC123"},
            url="https://www.instagram.com/creator/reel/ABC123/",
        )

        self.assertEqual(result.views, 2000)
        self.assertEqual(result.follower_count, 12345)
        self.extractor._fetch_counts_from_profile.assert_called_once_with(
            username="creator",
            shortcode="ABC123",
        )

    def test_extracts_nested_follower_count_from_direct_payload(self):
        follower_count = self.extractor._extract_follower_count(
            {
                "owner": {
                    "username": "creator",
                    "edge_followed_by": {"count": 9876},
                }
            }
        )

        self.assertEqual(follower_count, 9876)

    def test_extracts_profile_api_follower_count_from_modern_field(self):
        follower_count = self.extractor._extract_profile_follower_count(
            {
                "data": {
                    "user": {
                        "username": "creator",
                        "follower_count": 555,
                    }
                }
            }
        )

        self.assertEqual(follower_count, 555)

    def test_media_info_still_runs_when_profile_info_is_rate_limited(self):
        self.extractor._fetch_profile_info = Mock(return_value=None)
        self.extractor._fetch_media_info = Mock(
            return_value={
                "items": [
                    {
                        "code": "ABC123",
                        "play_count": 4444,
                        "like_count": 100,
                        "comment_count": 8,
                        "user": {"id": "25025320", "username": "creator"},
                    }
                ]
            }
        )
        self.extractor._fetch_user_info = Mock(return_value=None)
        self.extractor._fetch_public_page_counts = Mock(return_value=None)
        self.extractor._fetch_user_clips = Mock(return_value=None)
        self.extractor._log_profile_payload_summary = Mock()
        self.extractor._log_profile_candidate_nodes = Mock()

        counts = self.extractor._fetch_counts_from_profile(
            username="creator",
            shortcode="ABC123",
        )

        self.assertEqual(counts["views"], 4444)
        self.assertEqual(counts["likes"], 100)
        self.assertEqual(counts["comments"], 8)
        self.extractor._fetch_media_info.assert_called_once_with(
            shortcode="ABC123",
            username="creator",
        )
        self.extractor._fetch_user_clips.assert_not_called()

    def test_fetches_followers_by_user_id_when_profile_info_is_rate_limited(self):
        self.extractor._fetch_profile_info = Mock(return_value=None)
        self.extractor._fetch_media_info = Mock(
            return_value={
                "items": [
                    {
                        "code": "ABC123",
                        "play_count": 4444,
                        "user": {"id": "25025320", "username": "creator"},
                    }
                ]
            }
        )
        self.extractor._fetch_user_info = Mock(
            return_value={
                "user": {
                    "id": "25025320",
                    "username": "creator",
                    "follower_count": 685808762,
                },
                "status": "ok",
            }
        )
        self.extractor._fetch_public_page_counts = Mock(return_value=None)
        self.extractor._fetch_user_clips = Mock(return_value=None)
        self.extractor._log_profile_payload_summary = Mock()
        self.extractor._log_profile_candidate_nodes = Mock()

        counts = self.extractor._fetch_counts_from_profile(
            username="creator",
            shortcode="ABC123",
        )

        self.assertEqual(counts["follower_count"], 685808762)
        self.extractor._fetch_user_info.assert_called_once_with(
            user_id="25025320",
            username="creator",
        )
        self.extractor._fetch_user_clips.assert_not_called()

    def test_extracts_profile_user_id_from_media_info_payload(self):
        user_id = self.extractor._extract_profile_user_id(
            {
                "items": [
                    {
                        "user": {
                            "id": "25025320",
                            "username": "creator",
                        }
                    }
                ]
            }
        )

        self.assertEqual(user_id, "25025320")

    def test_extracts_root_user_info_follower_count(self):
        follower_count = self.extractor._extract_profile_follower_count(
            {
                "user": {
                    "username": "creator",
                    "follower_count": 685808762,
                },
                "status": "ok",
            }
        )

        self.assertEqual(follower_count, 685808762)

    def test_public_page_counts_fill_when_api_routes_fail(self):
        self.extractor._fetch_profile_info = Mock(return_value=None)
        self.extractor._fetch_media_info = Mock(return_value=None)
        self.extractor._fetch_user_info = Mock(return_value=None)
        self.extractor._fetch_public_page_counts = Mock(
            return_value={
                "follower_count": 12000,
                "views": 34000,
                "likes": None,
                "comments": None,
            }
        )

        counts = self.extractor._fetch_counts_from_profile(
            username="creator",
            shortcode="ABC123",
        )

        self.assertEqual(counts["follower_count"], 12000)
        self.assertEqual(counts["views"], 34000)

    def test_parses_compact_followers_from_public_profile_text(self):
        followers = self.extractor._extract_followers_from_page_text(
            '<meta name="description" content="12.4K Followers, 10 Following, 9 Posts">'
        )

        self.assertEqual(followers, 12400)

    def test_parses_public_reel_page_view_count(self):
        views = self.extractor._extract_first_regex_count(
            '{"play_count":56789}',
            (r'"play_count"\s*:\s*(\d+)',),
        )

        self.assertEqual(views, 56789)
