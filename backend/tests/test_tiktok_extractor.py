from unittest import TestCase
from unittest.mock import Mock

from app.services.extractors.tiktok_extractor import TikTokVideoExtractor


class TikTokVideoExtractorTests(TestCase):
    def setUp(self):
        self.extractor = TikTokVideoExtractor.__new__(TikTokVideoExtractor)

    def test_maps_nested_web_metadata(self):
        info = {
            "id": "7637113929105231124",
            "desc": "A clean TikTok hook #surf",
            "authorInfo": {
                "uniqueId": "creator_handle",
                "authorId": "12345",
                "nickname": "Creator Name",
            },
            "authorStats": {"followerCount": "98765"},
            "stats": {
                "playCount": "1000",
                "diggCount": "90",
                "commentCount": "10",
                "shareCount": "7",
                "collectCount": "3",
            },
            "textExtra": [{"hashtagName": "fyp"}],
            "track": "original sound",
            "artists": ["Creator Name"],
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@creator_handle/video/7637113929105231124",
            video_id="B",
        )

        self.assertEqual(metadata.platform_id, "7637113929105231124")
        self.assertEqual(metadata.title, "A clean TikTok hook #surf")
        self.assertEqual(metadata.creator, "creator_handle")
        self.assertEqual(metadata.creator_id, "12345")
        self.assertEqual(metadata.follower_count, 98765)
        self.assertEqual(metadata.views, 1000)
        self.assertEqual(metadata.likes, 90)
        self.assertEqual(metadata.comments, 10)
        self.assertEqual(metadata.engagement_rate, 10.0)
        self.assertIn("#surf", metadata.hashtags)
        self.assertIn("#fyp", metadata.hashtags)
        self.assertEqual(metadata.raw["share_count"], 7)
        self.assertEqual(metadata.raw["save_count"], 3)

    def test_maps_app_metadata(self):
        info = {
            "id": "7637113929105231124",
            "description": "App API description",
            "author": {
                "unique_id": "app_creator",
                "uid": "999",
                "follower_count": 321,
            },
            "statistics": {
                "play_count": 200,
                "digg_count": 20,
                "comment_count": 5,
            },
            "challenges": [{"title": "learn"}],
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@app_creator/video/7637113929105231124",
            video_id="A",
        )

        self.assertEqual(metadata.creator, "app_creator")
        self.assertEqual(metadata.creator_id, "999")
        self.assertEqual(metadata.follower_count, 321)
        self.assertEqual(metadata.views, 200)
        self.assertEqual(metadata.likes, 20)
        self.assertEqual(metadata.comments, 5)
        self.assertIn("#learn", metadata.hashtags)

    def test_fetches_followers_from_profile_when_video_payload_omits_them(self):
        self.extractor._fetch_profile_counts = Mock(
            return_value={"follower_count": 456789}
        )
        self.extractor._log_follower_debug_shape = Mock()
        info = {
            "id": "7637113929105231124",
            "description": "Video without follower count",
            "uploader": "creator_handle",
            "uploader_id": "12345",
            "view_count": 1000,
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@creator_handle/video/7637113929105231124",
            video_id="C",
        )

        self.assertEqual(metadata.follower_count, 456789)
        self.extractor._fetch_profile_counts.assert_called_once_with("creator_handle")

    def test_profile_fallback_prefers_url_handle_over_display_name(self):
        self.extractor._fetch_profile_counts = Mock(
            return_value={"follower_count": 456789}
        )
        self.extractor._log_follower_debug_shape = Mock()
        info = {
            "id": "7637113929105231124",
            "description": "Video without follower count",
            "uploader": "Creator Display Name",
            "view_count": 1000,
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@real.creator/video/7637113929105231124",
            video_id="C",
        )

        self.assertEqual(metadata.creator, "Creator Display Name")
        self.assertEqual(metadata.raw["profile_username"], "real.creator")
        self.assertEqual(metadata.follower_count, 456789)
        self.extractor._fetch_profile_counts.assert_called_once_with("real.creator")

    def test_keeps_direct_follower_count_without_profile_fetch(self):
        self.extractor._fetch_profile_counts = Mock()
        info = {
            "id": "7637113929105231124",
            "uploader": "creator_handle",
            "follower_count": 123,
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@creator_handle/video/7637113929105231124",
            video_id="D",
        )

        self.assertEqual(metadata.follower_count, 123)
        self.extractor._fetch_profile_counts.assert_not_called()

    def test_extracts_username_from_tiktok_url(self):
        username = self.extractor._extract_username_from_url(
            "https://www.tiktok.com/@real.creator/video/7637113929105231124"
        )

        self.assertEqual(username, "real.creator")

    def test_fetch_profile_page_uses_ytdlp_before_urllib(self):
        self.extractor._fetch_profile_page_text_with_ytdlp = Mock(
            return_value="<html>profile</html>"
        )
        self.extractor._fetch_profile_page_text_with_urllib = Mock()

        text = self.extractor._fetch_profile_page_text("real.creator")

        self.assertEqual(text, "<html>profile</html>")
        self.extractor._fetch_profile_page_text_with_ytdlp.assert_called_once_with(
            "https://www.tiktok.com/@real.creator"
        )
        self.extractor._fetch_profile_page_text_with_urllib.assert_not_called()

    def test_fetch_profile_page_falls_back_to_urllib(self):
        self.extractor._fetch_profile_page_text_with_ytdlp = Mock(return_value=None)
        self.extractor._fetch_profile_page_text_with_urllib = Mock(
            return_value="<html>fallback</html>"
        )

        text = self.extractor._fetch_profile_page_text("real.creator")

        self.assertEqual(text, "<html>fallback</html>")
        self.extractor._fetch_profile_page_text_with_urllib.assert_called_once_with(
            "https://www.tiktok.com/@real.creator"
        )

    def test_parses_profile_follower_count_from_universal_data(self):
        follower_count = self.extractor._extract_follower_count_from_profile_text(
            """
            <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
            {
              "__DEFAULT_SCOPE__": {
                "webapp.user-detail": {
                  "userInfo": {
                    "stats": {
                      "followerCount": 987654
                    }
                  }
                }
              }
            }
            </script>
            """
        )

        self.assertEqual(follower_count, 987654)

    def test_parses_profile_follower_count_from_regex_fallback(self):
        follower_count = self.extractor._extract_follower_count_from_profile_text(
            '{"statsV2":{"followerCount":"123456"}}'
        )

        self.assertEqual(follower_count, 123456)

    def test_maps_aweme_nested_follower_count(self):
        info = {
            "id": "7637113929105231124",
            "desc": "Nested aweme payload",
            "aweme_detail": {
                "author": {
                    "unique_id": "creator_handle",
                    "uid": "12345",
                    "follower_count": "12.4K",
                }
            },
            "stats": {
                "playCount": "1000",
            },
        }

        metadata = self.extractor._map_to_metadata(
            info=info,
            url="https://www.tiktok.com/@creator_handle/video/7637113929105231124",
            video_id="E",
        )

        self.assertEqual(metadata.follower_count, 12400)

    def test_parses_escaped_compact_profile_follower_count(self):
        follower_count = self.extractor._extract_follower_count_from_profile_text(
            r'{\"statsV2\":{\"followerCount\":\"12.4K\"}}'
        )

        self.assertEqual(follower_count, 12400)
