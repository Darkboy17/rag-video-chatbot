from app.schemas.video import VideoMetadata
from app.services.extractors.instagram_extractor import InstagramVideoExtractor
from app.services.extractors.tiktok_extractor import TikTokVideoExtractor
from app.services.extractors.youtube_extractor import YouTubeVideoExtractor
from app.utils.url_utils import detect_social_platform


class UnsupportedPlatformError(ValueError):
    """Raised when a URL is not from a supported social video platform."""

    pass


class VideoExtractor:
    """
    Dispatches metadata extraction to the correct platform service.
    """

    def __init__(self):
        self.extractors = {
            "youtube": YouTubeVideoExtractor(),
            "tiktok": TikTokVideoExtractor(),
            "instagram": InstagramVideoExtractor(),
        }

    def extract_metadata(self, url: str, video_id: str) -> VideoMetadata:
        platform = detect_social_platform(url)
        extractor = self.extractors.get(platform)

        if not extractor:
            raise UnsupportedPlatformError(
                "Unsupported video URL. Use a YouTube, TikTok, or Instagram URL."
            )

        return extractor.extract_metadata(url=url, video_id=video_id)
