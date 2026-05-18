import json
import logging
import re
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

import yt_dlp

from app.services.extractors.base import BaseYtDlpVideoExtractor
from app.schemas.video import VideoMetadata

logger = logging.getLogger(__name__)


class TikTokVideoExtractor(BaseYtDlpVideoExtractor):
    """
    Extracts metadata for public TikTok URLs.

    TikTok metadata is less consistent than YouTube, so this class checks
    TikTok-specific author fields before falling back to the generic yt-dlp
    names.
    """

    platform_name = "tiktok"
    blocked_reason = (
        "TikTok metadata extraction failed. The video may be private, region "
        "blocked, deleted, or blocked by TikTok's anti-bot checks."
    )

    def _extract_title(self, info: Dict[str, Any]) -> str | None:
        """
        Extract TikTok title text from description-style metadata fields.
        """

        return self._first_text(
            info.get("description"),
            info.get("title"),
            self._path(info, "aweme_detail", "desc"),
            self._path(info, "desc"),
        )

    def _extract_creator(self, info: Dict[str, Any]) -> str | None:
        """
        Extract the creator handle or display name from TikTok metadata shapes.
        """

        return self._first_text(
            info.get("uploader")
            or info.get("creator"),
            info.get("channel"),
            info.get("artist"),
            self._path(info, "author", "unique_id"),
            self._path(info, "author", "nickname"),
            self._path(info, "authorInfo", "uniqueId"),
            self._path(info, "authorInfo", "nickname"),
        )

    def _extract_creator_id(self, info: Dict[str, Any]) -> str | None:
        """
        Extract a stable TikTok author ID when the payload exposes one.
        """

        return self._first_text(
            info.get("uploader_id")
            or info.get("creator_id"),
            info.get("channel_id"),
            self._path(info, "author", "uid"),
            self._path(info, "author", "id"),
            self._path(info, "authorInfo", "authorId"),
            self._path(info, "authorInfo", "uid"),
            info.get("uploader"),
        )

    def _extract_follower_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract creator follower count from known TikTok author stats fields.
        """

        return self._first_int(
            info.get("channel_follower_count"),
            info.get("uploader_follower_count"),
            info.get("creator_follower_count"),
            info.get("follower_count"),
            info.get("followers_count"),
            info.get("fans"),
            info.get("fans_count"),
            info.get("fansCount"),
            self._path(info, "authorStats", "followerCount"),
            self._path(info, "authorStats", "follower_count"),
            self._path(info, "authorStats", "followers_count"),
            self._path(info, "authorStats", "fans"),
            self._path(info, "authorStats", "fansCount"),
            self._path(info, "author", "follower_count"),
            self._path(info, "author", "followerCount"),
            self._path(info, "author", "followers_count"),
            self._path(info, "author", "fans"),
            self._path(info, "author", "fansCount"),
            self._path(info, "authorInfo", "followerCount"),
            self._path(info, "authorInfo", "follower_count"),
            self._path(info, "authorInfo", "followers_count"),
            self._path(info, "authorInfo", "fans"),
            self._path(info, "authorInfo", "fansCount"),
            self._path(info, "aweme_detail", "author", "follower_count"),
            self._path(info, "aweme_detail", "author", "followerCount"),
            self._path(info, "aweme_detail", "author", "followers_count"),
            self._path(info, "aweme_detail", "author", "fans"),
            self._path(info, "aweme_detail", "author", "fansCount"),
            self._path(info, "aweme_detail", "authorStats", "followerCount"),
            self._path(info, "aweme_detail", "authorStats", "follower_count"),
            self._path(info, "aweme_detail", "authorStats", "fans"),
            self._path(info, "aweme_detail", "authorStats", "fansCount"),
            self._first_int_from_nested_keys(
                info,
                "followerCount",
                "follower_count",
                "followers_count",
                "fans",
                "fansCount",
                "fans_count",
            ),
        )

    def _extract_view_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract TikTok play count from common web and app payload fields.
        """

        return self._first_int(
            info.get("view_count"),
            info.get("play_count"),
            self._path(info, "stats", "playCount"),
            self._path(info, "stats", "play_count"),
            self._path(info, "statsV2", "playCount"),
            self._path(info, "statistics", "play_count"),
            self._path(info, "statistics", "playCount"),
        )

    def _extract_like_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract TikTok like count, also known as digg count in TikTok payloads.
        """

        return self._first_int(
            info.get("like_count"),
            info.get("digg_count"),
            self._path(info, "stats", "diggCount"),
            self._path(info, "stats", "digg_count"),
            self._path(info, "statsV2", "diggCount"),
            self._path(info, "statistics", "digg_count"),
            self._path(info, "statistics", "diggCount"),
        )

    def _extract_comment_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract TikTok comment count from flat or nested stats fields.
        """

        return self._first_int(
            info.get("comment_count"),
            self._path(info, "stats", "commentCount"),
            self._path(info, "stats", "comment_count"),
            self._path(info, "statsV2", "commentCount"),
            self._path(info, "statistics", "comment_count"),
            self._path(info, "statistics", "commentCount"),
        )

    def _extract_hashtags(self, info: Dict[str, Any]) -> List[str]:
        """
        Combine generic hashtags with TikTok-specific challenge metadata.
        """

        hashtags = super()._extract_hashtags(info)

        for tag in self._iter_tiktok_hashtags(info):
            if tag not in hashtags:
                hashtags.append(tag)

        return hashtags

    def _postprocess_metadata(
        self,
        metadata: VideoMetadata,
        info: Dict[str, Any],
        url: str,
    ) -> VideoMetadata:
        """
        Add TikTok-only metadata and optionally fill missing follower counts.
        """

        profile_username = self._profile_username(
            metadata=metadata,
            info=info,
            url=url,
        )

        if metadata.follower_count is None:
            self._log_follower_debug_shape(
                info=info,
                url=url,
                profile_username=profile_username,
            )

        if metadata.follower_count is None and profile_username:
            profile_counts = self._fetch_profile_counts(profile_username)
            if profile_counts.get("follower_count") is not None:
                metadata.follower_count = profile_counts["follower_count"]

        metadata.raw.update(
            {
                "uploader_url": info.get("uploader_url"),
                "channel_url": info.get("channel_url"),
                "track": info.get("track"),
                "artists": info.get("artists"),
                "share_count": self._extract_share_count(info),
                "save_count": self._extract_save_count(info),
                "profile_username": profile_username,
            }
        )

        return metadata

    def _fetch_profile_counts(self, username: str) -> dict[str, int | None]:
        """
        Fetch TikTok profile HTML and extract fallback creator stats from it.
        """

        counts = {
            "follower_count": None,
        }
        profile_text = self._fetch_profile_page_text(username)

        if not profile_text:
            metadata_status = "profile_unavailable"
        else:
            logger.info(
                "[tiktok] profile page shape creator=%s has_universal_data=%s "
                "has_next_data=%s has_follower_text=%s",
                username,
                "__UNIVERSAL_DATA_FOR_REHYDRATION__" in profile_text,
                "__NEXT_DATA__" in profile_text,
                "followerCount" in profile_text
                or "follower_count" in profile_text
                or "fansCount" in profile_text,
            )
            counts["follower_count"] = self._extract_follower_count_from_profile_text(
                profile_text
            )
            metadata_status = (
                "profile_count_available"
                if counts["follower_count"] is not None
                else "profile_count_unavailable"
            )

        logger.info(
            "[tiktok] profile fallback creator=%s followers=%s status=%s",
            username,
            counts["follower_count"],
            metadata_status,
        )

        return counts

    def _fetch_profile_page_text(self, username: str) -> str | None:
        """
        Download a public TikTok profile page for fallback metadata parsing.
        """

        encoded_username = quote(username.strip().lstrip("@"))
        profile_url = f"https://www.tiktok.com/@{encoded_username}"
        ytdlp_text = self._fetch_profile_page_text_with_ytdlp(profile_url)
        if ytdlp_text:
            return ytdlp_text

        return self._fetch_profile_page_text_with_urllib(profile_url)

    def _fetch_profile_page_text_with_ytdlp(self, profile_url: str) -> str | None:
        """
        Fetch profile HTML through yt-dlp so cookies and impersonation can apply.
        """

        options = self._build_ydl_options(download=False)
        options.update(
            {
                "extract_flat": True,
                "skip_download": True,
            }
        )

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                response = ydl.urlopen(profile_url)
                payload = response.read()
                payload_text = payload.decode("utf-8", errors="ignore")
                logger.info(
                    "[tiktok] TikTok profile yt-dlp response url=%s status=%s bytes=%s",
                    profile_url,
                    getattr(response, "status", "unknown"),
                    len(payload_text),
                )
                self._log_profile_preview_if_empty(profile_url, payload_text)
                return payload_text
        except Exception as exc:
            logger.info(
                "[tiktok] TikTok profile yt-dlp request failed url=%s error=%s",
                profile_url,
                exc,
            )
            return None

    def _fetch_profile_page_text_with_urllib(self, profile_url: str) -> str | None:
        """
        Raw HTTP fallback used when yt-dlp cannot fetch the profile page.
        """

        request = Request(
            profile_url,
            headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Referer": "https://www.tiktok.com/",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload_text = response.read().decode("utf-8", errors="ignore")
                logger.info(
                    "[tiktok] TikTok profile response url=%s status=%s bytes=%s",
                    profile_url,
                    getattr(response, "status", "unknown"),
                    len(payload_text),
                )
                return payload_text
        except HTTPError as exc:
            logger.info(
                "[tiktok] TikTok profile request failed url=%s status=%s",
                profile_url,
                exc.code,
            )
            return None
        except (URLError, TimeoutError, OSError) as exc:
            logger.info(
                "[tiktok] TikTok profile request failed url=%s error=%s",
                profile_url,
                exc,
            )
            return None

    def _log_profile_preview_if_empty(self, profile_url: str, payload_text: str) -> None:
        """
        Log a tiny preview when TikTok returns shell/challenge HTML.
        """

        has_profile_data = (
            "__UNIVERSAL_DATA_FOR_REHYDRATION__" in payload_text
            or "__NEXT_DATA__" in payload_text
            or "followerCount" in payload_text
            or "follower_count" in payload_text
            or "fansCount" in payload_text
        )

        if has_profile_data:
            return

        preview = re.sub(r"\s+", " ", payload_text[:300]).strip()
        logger.info(
            "[tiktok] TikTok profile response missing embedded stats url=%s preview=%s",
            profile_url,
            preview,
        )

    def _profile_username(
        self,
        metadata: VideoMetadata,
        info: Dict[str, Any],
        url: str,
    ) -> str | None:
        """
        Choose the best TikTok handle for profile-page fallback requests.
        """

        return self._first_text(
            self._extract_username_from_url(url),
            self._path(info, "author", "unique_id"),
            self._path(info, "authorInfo", "uniqueId"),
            self._path(info, "aweme_detail", "author", "unique_id"),
            info.get("uploader_id"),
            info.get("channel_id"),
            metadata.creator,
        )

    def _extract_username_from_url(self, url: str) -> str | None:
        """
        Extract the @handle from a canonical TikTok URL.
        """

        parsed = urlparse(url)
        match = re.search(r"/@([^/?#]+)", parsed.path)
        if not match:
            return None

        return unquote(match.group(1)).strip() or None

    def _log_follower_debug_shape(
        self,
        info: Dict[str, Any],
        url: str,
        profile_username: str | None,
    ) -> None:
        """
        Log compact TikTok metadata shape details without dumping the full payload.
        """

        nested_key_sets = {
            "author": self._dict_keys(info.get("author")),
            "authorInfo": self._dict_keys(info.get("authorInfo")),
            "authorStats": self._dict_keys(info.get("authorStats")),
            "stats": self._dict_keys(info.get("stats")),
            "statsV2": self._dict_keys(info.get("statsV2")),
            "statistics": self._dict_keys(info.get("statistics")),
            "aweme_author": self._dict_keys(
                self._path(info, "aweme_detail", "author")
            ),
            "aweme_authorStats": self._dict_keys(
                self._path(info, "aweme_detail", "authorStats")
            ),
        }
        candidate_values = {
            path: value
            for path, value in {
                "follower_count": info.get("follower_count"),
                "followers_count": info.get("followers_count"),
                "fans": info.get("fans"),
                "fansCount": info.get("fansCount"),
                "authorStats.followerCount": self._path(
                    info, "authorStats", "followerCount"
                ),
                "authorStats.fansCount": self._path(
                    info, "authorStats", "fansCount"
                ),
                "author.follower_count": self._path(
                    info, "author", "follower_count"
                ),
                "author.followerCount": self._path(
                    info, "author", "followerCount"
                ),
                "authorInfo.followerCount": self._path(
                    info, "authorInfo", "followerCount"
                ),
                "aweme_detail.author.follower_count": self._path(
                    info, "aweme_detail", "author", "follower_count"
                ),
                "aweme_detail.author.followerCount": self._path(
                    info, "aweme_detail", "author", "followerCount"
                ),
                "aweme_detail.authorStats.followerCount": self._path(
                    info, "aweme_detail", "authorStats", "followerCount"
                ),
            }.items()
            if value is not None
        }

        logger.info(
            "[tiktok] follower debug url=%s profile_username=%s top_keys=%s "
            "nested_keys=%s follower_candidates=%s",
            url,
            profile_username,
            sorted(info.keys()),
            nested_key_sets,
            candidate_values,
        )

    def _dict_keys(self, value: Any) -> list[str]:
        if not isinstance(value, dict):
            return []

        return sorted(str(key) for key in value.keys())

    def _extract_follower_count_from_profile_text(self, text: str) -> int | None:
        """
        Parse follower count from embedded profile JSON or regex fallbacks.
        """

        for data in self._iter_embedded_json_payloads(text):
            follower_count = self._first_int_from_nested_keys(
                data,
                "followerCount",
                "follower_count",
                "followers_count",
                "fans",
                "fansCount",
                "fans_count",
            )

            if follower_count is not None:
                return follower_count

        return self._extract_first_regex_count(
            text,
            (
                r'\\?"followerCount\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
                r'\\?"follower_count\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
                r'\\?"followers_count\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
                r'\\?"fansCount\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
                r'\\?"fans_count\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
                r'\\?"fans\\?"\s*:\s*\\?"?([\d,.]+\s*[KMB]?)\\?"?',
            ),
        )

    def _iter_embedded_json_payloads(self, text: str) -> Iterable[Any]:
        """
        Yield JSON payloads embedded in TikTok profile script tags.
        """

        for script_id in ("__UNIVERSAL_DATA_FOR_REHYDRATION__", "__NEXT_DATA__"):
            match = re.search(
                rf'<script[^>]+id=["\']{script_id}["\'][^>]*>(.*?)</script>',
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if not match:
                continue

            try:
                yield json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    def _extract_share_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract TikTok share or repost count for raw metadata enrichment.
        """

        return self._first_int(
            info.get("repost_count"),
            info.get("share_count"),
            self._path(info, "stats", "shareCount"),
            self._path(info, "stats", "share_count"),
            self._path(info, "statistics", "share_count"),
        )

    def _extract_save_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract TikTok save or collect count for raw metadata enrichment.
        """

        return self._first_int(
            info.get("save_count"),
            info.get("collect_count"),
            self._path(info, "stats", "collectCount"),
            self._path(info, "stats", "collect_count"),
            self._path(info, "statistics", "collect_count"),
        )

    def _iter_tiktok_hashtags(self, info: Dict[str, Any]) -> Iterable[str]:
        """
        Yield hashtags from TikTok challenge, textExtra, and description fields.
        """

        for challenge in self._as_list(info.get("challenges")):
            tag = self._first_text(
                self._path(challenge, "title"),
                self._path(challenge, "cha_name"),
                self._path(challenge, "hashtagName"),
            )
            if tag:
                yield self._normalize_hashtag(tag)

        for text_extra in self._as_list(info.get("textExtra")):
            tag = self._first_text(
                self._path(text_extra, "hashtagName"),
                self._path(text_extra, "hashtag_name"),
            )
            if tag:
                yield self._normalize_hashtag(tag)

        description = (
            info.get("description")
            or info.get("title")
            or info.get("desc")
            or self._path(info, "aweme_detail", "desc")
            or ""
        )
        for match in re.finditer(r"(?<!\w)#([\w_]+)", str(description)):
            yield self._normalize_hashtag(match.group(1))
