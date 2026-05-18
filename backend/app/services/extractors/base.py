import re
from typing import Any, Dict, Iterable, List

import yt_dlp

from app.core.config import get_settings
from app.schemas.video import VideoMetadata
from app.services.media.ytdlp_options import apply_common_ytdlp_options
from app.utils.url_utils import safe_int


class BaseYtDlpVideoExtractor:
    """
    Shared yt-dlp integration for platform-specific metadata extractors.

    Subclasses keep platform decisions explicit while this base class centralizes
    the mechanics that are identical across YouTube, TikTok, and Instagram.
    """

    platform_name = "unknown"
    blocked_reason = "yt-dlp could not extract metadata for this URL."

    def __init__(self):
        """
        Load application settings used to configure yt-dlp requests.
        """

        self.settings = get_settings()

    def extract_metadata(self, url: str, video_id: str) -> VideoMetadata:
        """
        Fetch raw yt-dlp metadata and convert it into the app's video schema.
        """

        ydl_opts = self._build_ydl_options(download=False)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info: Dict[str, Any] = ydl.extract_info(url, download=False)

            return self._map_to_metadata(
                info=info,
                url=url,
                video_id=video_id,
            )

        except yt_dlp.utils.DownloadError as exc:
            return VideoMetadata(
                video_id=video_id,
                source_url=url,
                title="Metadata unavailable",
                raw={
                    "error": str(exc),
                    "platform": self.platform_name,
                    "reason": self.blocked_reason,
                },
            )

    def _build_ydl_options(self, download: bool) -> dict:
        """
        Build yt-dlp options for metadata extraction or media download.
        """

        options = {
            "quiet": True,
            "noprogress": True,
            "skip_download": not download,
            "noplaylist": True,
            "extract_flat": False,
        }

        return apply_common_ytdlp_options(options, self.settings)

    def _map_to_metadata(
        self,
        info: Dict[str, Any],
        url: str,
        video_id: str,
    ) -> VideoMetadata:
        """
        Map a raw yt-dlp info dictionary into normalized video metadata.
        """

        views = self._extract_view_count(info)
        likes = self._extract_like_count(info)
        comments = self._extract_comment_count(info)

        engagement_rate = self._compute_engagement_rate(
            likes=likes,
            comments=comments,
            views=views,
        )

        metadata = VideoMetadata(
            video_id=video_id,
            source_url=url,
            platform_id=info.get("id"),
            title=self._extract_title(info),
            creator=self._extract_creator(info),
            creator_id=self._extract_creator_id(info),
            follower_count=self._extract_follower_count(info),
            views=views,
            likes=likes,
            comments=comments,
            engagement_rate=engagement_rate,
            hashtags=self._extract_hashtags(info),
            upload_date=info.get("upload_date"),
            duration_seconds=safe_int(info.get("duration")),
            raw={
                "webpage_url": info.get("webpage_url"),
                "extractor": info.get("extractor"),
                "platform": self.platform_name,
                "thumbnail": info.get("thumbnail"),
                "description": info.get("description"),
            },
        )

        return self._postprocess_metadata(
            metadata=metadata,
            info=info,
            url=url,
        )

    def _postprocess_metadata(
        self,
        metadata: VideoMetadata,
        info: Dict[str, Any],
        url: str,
    ) -> VideoMetadata:
        """
        Allow subclasses to enrich metadata after the common mapping step.
        """

        return metadata

    def _extract_title(self, info: Dict[str, Any]) -> str | None:
        """
        Extract the display title from a raw yt-dlp metadata payload.
        """

        return info.get("title")

    def _extract_creator(self, info: Dict[str, Any]) -> str | None:
        """
        Extract the best available creator or channel name.
        """

        return info.get("uploader") or info.get("channel") or info.get("creator")

    def _extract_creator_id(self, info: Dict[str, Any]) -> str | None:
        """
        Extract a stable creator identifier when yt-dlp exposes one.
        """

        return (
            info.get("uploader_id")
            or info.get("channel_id")
            or info.get("creator_id")
            or info.get("uploader")
        )

    def _extract_follower_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract creator follower count from common yt-dlp field names.
        """

        return safe_int(
            info.get("channel_follower_count")
            or info.get("uploader_follower_count")
            or info.get("creator_follower_count")
            or info.get("follower_count")
        )

    def _extract_view_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract the video view count as an integer.
        """

        return safe_int(info.get("view_count"))

    def _extract_like_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract the video like count as an integer.
        """

        return safe_int(info.get("like_count"))

    def _extract_comment_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract the video comment count as an integer.
        """

        return safe_int(info.get("comment_count"))

    def _compute_engagement_rate(
        self,
        likes: int | None,
        comments: int | None,
        views: int | None,
    ) -> float | None:
        """
        Calculate engagement rate as likes plus comments divided by views.
        """

        if not views or views <= 0:
            return None

        likes = likes or 0
        comments = comments or 0

        return round(((likes + comments) / views) * 100, 4)

    def _extract_hashtags(self, info: Dict[str, Any]) -> List[str]:
        """
        Collect normalized hashtags from yt-dlp tags and the description text.
        """

        tags = info.get("tags") or []
        description = info.get("description") or ""

        hashtags: List[str] = []

        for tag in tags:
            cleaned = str(tag).strip()

            if not cleaned:
                continue

            if not cleaned.startswith("#"):
                cleaned = f"#{cleaned}"

            if cleaned not in hashtags:
                hashtags.append(cleaned)

        for hashtag in self._extract_description_hashtags(description):
            if hashtag not in hashtags:
                hashtags.append(hashtag)

        return hashtags

    def _extract_description_hashtags(self, description: str) -> List[str]:
        """
        Extract whitespace-delimited hashtags from a description string.
        """

        return [
            token
            for token in description.split()
            if token.startswith("#") and len(token) > 1
        ]

    def _normalize_hashtag(self, tag: str) -> str:
        """
        Convert a raw tag value into a single hashtag-prefixed string.
        """

        cleaned = tag.strip().lstrip("#")

        return f"#{cleaned}" if cleaned else ""

    def _first_text(self, *values: Any) -> str | None:
        """
        Return the first non-empty text value from several candidates.
        """

        for value in values:
            if value is None:
                continue

            text = str(value).strip()
            if text:
                return text

        return None

    def _first_int(self, *values: Any) -> int | None:
        """
        Return the first candidate that can be safely parsed as an integer.
        """

        for value in values:
            parsed = safe_int(value)
            if parsed is not None:
                return parsed

        return None

    def _count_value(self, value: Any) -> int | None:
        """
        Parse count values that may be raw numbers or nested count dictionaries.
        """

        if isinstance(value, dict):
            return safe_int(value.get("count") or value.get("total_count"))

        return safe_int(value)

    def _extract_first_regex_count(
        self,
        text: str,
        patterns: Iterable[str],
    ) -> int | None:
        """
        Return the first integer captured by any regex pattern.
        """

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return safe_int(match.group(1))

        return None

    def _first_int_from_nested_keys(
        self,
        value: Any,
        *keys: str,
    ) -> int | None:
        """
        Recursively search nested lists and dictionaries for count fields.
        """

        if isinstance(value, dict):
            for key in keys:
                parsed = self._count_value(value.get(key))
                if parsed is not None:
                    return parsed

            for child in value.values():
                parsed = self._first_int_from_nested_keys(child, *keys)
                if parsed is not None:
                    return parsed

        if isinstance(value, list):
            for child in value:
                parsed = self._first_int_from_nested_keys(child, *keys)
                if parsed is not None:
                    return parsed

        return None

    def _path(self, source: Any, *keys: str) -> Any:
        """
        Read a nested dictionary path without raising on missing branches.
        """

        current = source

        for key in keys:
            if not isinstance(current, dict):
                return None

            current = current.get(key)

        return current

    def _as_list(self, value: Any) -> list[Any]:
        """
        Return list values unchanged and treat all other values as empty.
        """

        if isinstance(value, list):
            return value

        return []
