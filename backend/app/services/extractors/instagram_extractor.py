import json
import logging
import re
from typing import Any, Dict, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

from yt_dlp.cookies import extract_cookies_from_browser

from app.services.extractors.base import BaseYtDlpVideoExtractor
from app.schemas.video import VideoMetadata
from app.utils.url_utils import safe_int

logger = logging.getLogger(__name__)
INSTAGRAM_SHORTCODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def _debug_log(*args, **kwargs) -> None:
    """
    Disabled Instagram diagnostic logger placeholder.
    """

    # Temporarily silence verbose Instagram extraction diagnostics.
    # Swap this to logger.info(*args, **kwargs) when debugging Instagram again.
    return None


class InstagramVideoExtractor(BaseYtDlpVideoExtractor):
    """
    Extracts metadata for public Instagram Reels.

    Instagram often omits counts or requires cookies. Missing fields remain
    unavailable instead of being fabricated.
    """

    platform_name = "instagram"
    blocked_reason = (
        "Instagram metadata extraction failed. The Reel may require login "
        "cookies, be private, deleted, or unavailable to this region."
    )

    def __init__(self):
        """
        Initialize shared extractor settings and the lazy browser cookie cache.
        """

        super().__init__()
        self._browser_cookie_jar = None

    def _extract_title(self, info: Dict[str, Any]) -> str | None:
        """
        Use the Instagram title when available, otherwise fall back to caption text.
        """

        return info.get("title") or info.get("description")

    def _extract_creator(self, info: Dict[str, Any]) -> str | None:
        """
        Extract the Instagram creator username from common yt-dlp fields.
        """

        return (
            info.get("channel")
            or info.get("uploader")
            or info.get("creator")
            or info.get("uploader_id")
        )

    def _extract_creator_id(self, info: Dict[str, Any]) -> str | None:
        """
        Extract a stable Instagram creator identifier or username fallback.
        """

        return (
            info.get("uploader_id")
            or info.get("channel_id")
            or info.get("creator_id")
            or info.get("uploader")
        )

    def _postprocess_metadata(
        self,
        metadata: VideoMetadata,
        info: Dict[str, Any],
        url: str,
    ) -> VideoMetadata:
        """
        Enrich direct yt-dlp metadata with Instagram profile and media counts.
        """

        shortcode = self._extract_shortcode(info=info, url=url)
        username = self._extract_profile_username(
            info) or self._extract_username_from_url(url)

        _debug_log(
            "[instagram] extracted direct metadata source_url=%s platform_id=%s "
            "shortcode=%s creator=%s likes=%s views=%s comments=%s",
            url,
            metadata.platform_id,
            shortcode,
            username,
            metadata.likes,
            metadata.views,
            metadata.comments,
        )

        if (
            metadata.views is not None
            and metadata.follower_count is not None
        ):
            return metadata

        if not shortcode or not username:
            metadata.raw["instagram_count_fallback"] = "missing_shortcode_or_username"
            _debug_log(
                "[instagram] skipped profile fallback source_url=%s platform_id=%s "
                "shortcode=%s creator=%s reason=missing_shortcode_or_username",
                url,
                metadata.platform_id,
                shortcode,
                username,
            )
            return metadata

        profile_counts = self._fetch_counts_from_profile(
            username=username,
            shortcode=shortcode,
        )

        if profile_counts:
            metadata.follower_count = (
                profile_counts.get("follower_count") or metadata.follower_count
            )
            metadata.views = profile_counts.get("views") or metadata.views
            metadata.likes = profile_counts.get("likes") or metadata.likes
            metadata.comments = profile_counts.get(
                "comments") or metadata.comments
            metadata.engagement_rate = self._compute_engagement_rate(
                likes=metadata.likes,
                comments=metadata.comments,
                views=metadata.views,
            )

        if (
            not profile_counts
            or (
                metadata.views is None
                and metadata.follower_count is None
            )
        ):
            metadata.raw["instagram_count_fallback"] = "profile_count_unavailable"
            _debug_log(
                "[instagram] profile fallback did not find counts source_url=%s "
                "platform_id=%s shortcode=%s creator=%s followers=%s likes=%s",
                url,
                metadata.platform_id,
                shortcode,
                username,
                metadata.follower_count,
                metadata.likes,
            )
            return metadata

        metadata.raw["instagram_count_fallback"] = "profile_or_media_api"
        _debug_log(
            "[instagram] profile fallback applied source_url=%s platform_id=%s "
            "shortcode=%s creator=%s followers=%s likes=%s views=%s",
            url,
            metadata.platform_id,
            shortcode,
            username,
            metadata.follower_count,
            metadata.likes,
            metadata.views,
        )

        return metadata

    def _extract_view_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract Instagram Reel play or view count from known count fields.
        """

        return self._first_int_from_info(
            info,
            "play_count",
            "video_play_count",
            "ig_play_count",
            "fb_play_count",
            "view_count",
            "video_view_count",
        )

    def _extract_like_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract Instagram like count from flat or nested like fields.
        """

        return self._first_int_from_info(
            info,
            "like_count",
            "edge_media_preview_like",
            "edge_liked_by",
            "likes",
        )

    def _extract_comment_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract Instagram comment count from flat or nested comment fields.
        """

        return self._first_int_from_info(
            info,
            "comment_count",
            "edge_media_to_comment",
            "edge_media_to_parent_comment",
            "comments",
        )

    def _extract_follower_count(self, info: Dict[str, Any]) -> int | None:
        """
        Extract follower count from generic fields or nested Instagram owner data.
        """

        return (
            super()._extract_follower_count(info)
            or self._first_int_from_nested_keys(
                info,
                "follower_count",
                "followers_count",
                "edge_followed_by",
            )
        )

    def _first_int_from_info(self, info: Dict[str, Any], *keys: str) -> int | None:
        """
        Instagram can return counts as flattened yt-dlp fields, nested count
        objects, or per-entry values for carousel/product responses.
        """

        for candidate in self._iter_candidate_infos(info):
            for key in keys:
                value = self._count_value(candidate.get(key))
                if value is not None:
                    return value

        return None

    def _iter_candidate_infos(self, info: Dict[str, Any]):
        """
        Yield the main info payload and entry payloads for carousel responses.
        """

        yield info

        entries = info.get("entries") or []
        if not isinstance(entries, list):
            return

        for entry in entries:
            if isinstance(entry, dict):
                yield entry

    def _extract_shortcode(self, info: Dict[str, Any], url: str) -> str | None:
        """
        Extract the Reel/post shortcode from metadata or the source URL.
        """

        candidate = info.get("id") or info.get(
            "display_id") or info.get("shortcode")

        if candidate:
            return str(candidate)

        match = re.search(r"/(?:reel|reels|p|tv)/([^/?#]+)/?", url)
        if match:
            return match.group(1)

        return None

    def _extract_profile_username(self, info: Dict[str, Any]) -> str | None:
        """
        Extract the profile username from metadata fields or embedded URLs.
        """

        username = (
            info.get("channel")
            or info.get("username")
            or info.get("uploader")
            or info.get("creator")
            or info.get("uploader_id")
            or info.get("channel_id")
        )

        if username:
            return str(username).lstrip("@")

        for url in (
            info.get("webpage_url"),
            info.get("original_url"),
            info.get("url"),
        ):
            if not url:
                continue

            match = re.search(
                r"instagram\.com/([^/]+)/(?:reel|reels|p|tv)/", str(url))
            if match:
                return match.group(1)

        return None

    def _extract_username_from_url(self, url: str) -> str | None:
        """
        Extract the creator username from an Instagram Reel URL.
        """

        match = re.search(
            r"instagram\.com/([^/]+)/(?:reel|reels|p|tv)/", url or "")
        if match:
            return match.group(1)

        return None

    def _fetch_counts_from_profile(
        self,
        username: str,
        shortcode: str,
    ) -> dict[str, int | None] | None:
        """
        Try multiple Instagram endpoints/pages to fill missing counts for a Reel.
        """

        counts: dict[str, int | None] = {
            "follower_count": None,
            "views": None,
            "likes": None,
            "comments": None,
        }
        profile_data = self._fetch_profile_info(username)
        user_id = None

        if profile_data:
            self._log_profile_payload_summary(
                username=username,
                profile_data=profile_data,
            )
            self._log_profile_candidate_nodes(
                username=username,
                profile_data=profile_data,
            )
            counts["follower_count"] = self._extract_profile_follower_count(
                profile_data
            )
            user_id = self._extract_profile_user_id(profile_data)

            profile_match = self._find_first_count_match(
                username=username,
                shortcode=shortcode,
                payload=profile_data,
                source="profile_info",
            )
            self._merge_count_result(counts, profile_match)

        media_info = self._fetch_media_info(
            shortcode=shortcode, username=username)

        if media_info:
            self._log_profile_payload_summary(
                username=username,
                profile_data=media_info,
            )
            self._log_profile_candidate_nodes(
                username=username,
                profile_data=media_info,
            )

            media_match = self._find_first_count_match(
                username=username,
                shortcode=shortcode,
                payload=media_info,
                source="media_info",
            )
            self._merge_count_result(counts, media_match)
            user_id = user_id or self._extract_profile_user_id(media_info)

        if user_id and counts.get("follower_count") is None:
            user_info = self._fetch_user_info(
                user_id=user_id, username=username)

            if user_info:
                follower_count = self._extract_profile_follower_count(
                    user_info)
                if follower_count is not None:
                    counts["follower_count"] = follower_count

        page_counts = self._fetch_public_page_counts(
            username=username,
            shortcode=shortcode,
        )
        self._merge_count_result(counts, page_counts)

        if counts.get("views") is not None:
            return counts

        if not user_id:
            _debug_log(
                "[instagram] cannot request clips feed creator=%s reason=missing_user_id",
                username,
            )
            return counts if self._has_any_count(counts) else None

        max_id = None

        for page_number in range(1, 26):
            clips_data = self._fetch_user_clips(
                username=username,
                user_id=user_id,
                max_id=max_id,
            )

            if not clips_data:
                break

            _debug_log(
                "[instagram] processing clips page creator=%s page=%s max_id=%s "
                "paging_info=%s",
                username,
                page_number,
                max_id,
                clips_data.get("paging_info") if isinstance(
                    clips_data, dict) else None,
            )

            self._log_profile_payload_summary(
                username=username,
                profile_data=clips_data,
            )
            self._log_profile_candidate_nodes(
                username=username,
                profile_data=clips_data,
            )

            clips_match = self._find_first_count_match(
                username=username,
                shortcode=shortcode,
                payload=clips_data,
                source="clips_feed",
            )

            if clips_match is not None:
                self._merge_count_result(counts, clips_match)
                return counts

            next_max_id = self._extract_clips_next_max_id(clips_data)

            if not next_max_id or next_max_id == max_id:
                break

            max_id = next_max_id

        _debug_log(
            "[instagram] target reel not found in paginated clips feed "
            "creator=%s shortcode=%s",
            username,
            shortcode,
        )

        return counts if self._has_any_count(counts) else None

    def _find_first_count_match(
        self,
        username: str,
        shortcode: str,
        payload: Dict[str, Any],
        source: str,
    ) -> dict[str, int | None] | None:
        """
        Find the target Reel node inside a payload and extract its visible counts.
        """

        matching_nodes = self._find_matching_shortcode_nodes(
            value=payload,
            shortcode=shortcode,
        )

        for node in matching_nodes:
            view_count = self._extract_profile_grid_view_count(node)
            like_count = self._extract_like_count(node)
            comment_count = self._extract_comment_count(node)
            node_platform_id = (
                node.get("shortcode")
                or node.get("code")
                or node.get("id")
            )

            _debug_log(
                "[instagram] matched creator node source=%s creator=%s "
                "target_shortcode=%s node_platform_id=%s node_likes=%s "
                "node_views=%s node_count_candidates=%s",
                source,
                username,
                shortcode,
                node_platform_id,
                like_count,
                view_count,
                self._debug_count_candidates(node),
            )

            if view_count is not None:
                count_candidates = self._debug_count_candidates(node)

                if not self._has_profile_play_count(count_candidates):
                    _debug_log(
                        "[instagram] matched node has no profile-grid play count "
                        "source=%s creator=%s target_shortcode=%s candidates=%s",
                        source,
                        username,
                        shortcode,
                        count_candidates,
                    )

                return {
                    "views": view_count,
                    "likes": like_count,
                    "comments": comment_count,
                }

        return None

    def _fetch_profile_info(self, username: str) -> Dict[str, Any] | None:
        """
        Fetch Instagram web profile JSON for a public username.
        """

        encoded_username = quote(username.strip().lstrip("@"))
        profile_url = (
            "https://www.instagram.com/api/v1/users/web_profile_info/"
            f"?username={encoded_username}"
        )
        _debug_log("[instagram] visiting creator profile url=%s", profile_url)

        return self._fetch_instagram_json(
            url=profile_url,
            referer=f"https://www.instagram.com/{encoded_username}/",
        )

    def _fetch_media_info(
        self,
        shortcode: str,
        username: str,
    ) -> Dict[str, Any] | None:
        """
        Fetch Instagram media info JSON using the numeric media primary key.
        """

        media_pk = self._shortcode_to_media_pk(shortcode)

        if not media_pk:
            return None

        media_info_url = f"https://www.instagram.com/api/v1/media/{media_pk}/info/"
        _debug_log("[instagram] visiting media info url=%s", media_info_url)

        return self._fetch_instagram_json(
            url=media_info_url,
            referer=f"https://www.instagram.com/{username}/reel/{shortcode}/",
        )

    def _fetch_user_info(
        self,
        user_id: str,
        username: str,
    ) -> Dict[str, Any] | None:
        """
        Fetch Instagram user info JSON by internal user ID.
        """

        user_info_url = f"https://www.instagram.com/api/v1/users/{user_id}/info/"
        _debug_log(
            "[instagram] visiting creator user info url=%s", user_info_url)

        return self._fetch_instagram_json(
            url=user_info_url,
            referer=f"https://www.instagram.com/{quote(username.strip().lstrip('@'))}/",
        )

    def _fetch_user_clips(
        self,
        username: str,
        user_id: str,
        max_id: str | None = None,
    ) -> Dict[str, Any] | None:
        """
        Fetch a page of the creator's Reel clips feed for matching media counts.
        """

        encoded_username = quote(username.strip().lstrip("@"))
        clips_url = "https://www.instagram.com/api/v1/clips/user/"
        form_data = {
            "target_user_id": str(user_id),
            "page_size": "12",
            "include_feed_video": "true",
        }

        if max_id:
            form_data["max_id"] = max_id

        _debug_log("[instagram] visiting creator clips url=%s", clips_url)

        return self._fetch_instagram_json(
            url=clips_url,
            referer=f"https://www.instagram.com/{encoded_username}/reels/",
            form_data=form_data,
        )

    def _fetch_public_page_counts(
        self,
        username: str,
        shortcode: str,
    ) -> dict[str, int | None] | None:
        """
        Scrape public profile and Reel pages for count values as a fallback.
        """

        counts: dict[str, int | None] = {
            "follower_count": None,
            "views": None,
            "likes": None,
            "comments": None,
        }
        encoded_username = quote(username.strip().lstrip("@"))
        encoded_shortcode = quote(shortcode)

        profile_text = self._fetch_instagram_page_text(
            url=f"https://www.instagram.com/{encoded_username}/",
            referer="https://www.instagram.com/",
        )
        if profile_text:
            counts["follower_count"] = self._extract_followers_from_page_text(
                profile_text
            )

        reel_text = self._fetch_instagram_page_text(
            url=f"https://www.instagram.com/reel/{encoded_shortcode}/",
            referer=f"https://www.instagram.com/{encoded_username}/",
        )
        if reel_text:
            counts["views"] = self._extract_first_regex_count(
                reel_text,
                (
                    r'"play_count"\s*:\s*(\d+)',
                    r'"video_play_count"\s*:\s*(\d+)',
                    r'"video_view_count"\s*:\s*(\d+)',
                    r'"view_count"\s*:\s*(\d+)',
                ),
            )
            counts["likes"] = self._extract_first_regex_count(
                reel_text,
                (
                    r'"like_count"\s*:\s*(\d+)',
                    r'"edge_media_preview_like"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
                    r'"edge_liked_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
                ),
            )
            counts["comments"] = self._extract_first_regex_count(
                reel_text,
                (
                    r'"comment_count"\s*:\s*(\d+)',
                    r'"edge_media_to_comment"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
                    r'"edge_media_to_parent_comment"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
                ),
            )

        _debug_log(
            "[instagram] public page fallback creator=%s shortcode=%s "
            "followers=%s views=%s likes=%s comments=%s",
            username,
            shortcode,
            counts.get("follower_count"),
            counts.get("views"),
            counts.get("likes"),
            counts.get("comments"),
        )

        return counts if self._has_any_count(counts) else None

    def _fetch_instagram_page_text(
        self,
        url: str,
        referer: str,
        use_cookies: bool = True,
    ) -> str | None:
        """
        Fetch Instagram HTML with optional browser cookies and retry without them.
        """

        request = Request(
            url,
            headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Referer": referer,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
        )

        try:
            opener = self._build_cookie_opener() if use_cookies else None
            response_context = opener.open(request, timeout=10) if opener else urlopen(
                request,
                timeout=10,
            )
            with response_context as response:
                payload_text = response.read().decode("utf-8", errors="ignore")
                _debug_log(
                    "[instagram] Instagram page response url=%s status=%s bytes=%s",
                    url,
                    getattr(response, "status", "unknown"),
                    len(payload_text),
                )
                return payload_text
        except HTTPError as exc:
            _debug_log(
                "[instagram] Instagram page request failed url=%s status=%s",
                url,
                exc.code,
            )
            if use_cookies and exc.code in {401, 403, 429}:
                return self._fetch_instagram_page_text(
                    url=url,
                    referer=referer,
                    use_cookies=False,
                )
            return None
        except (URLError, TimeoutError, OSError) as exc:
            _debug_log(
                "[instagram] Instagram page request failed url=%s error=%s", url, exc)
            return None

    def _fetch_instagram_json(
        self,
        url: str,
        referer: str,
        form_data: Dict[str, str] | None = None,
        use_cookies: bool = True,
    ) -> Dict[str, Any] | None:
        """
        Fetch Instagram JSON endpoints with web headers and cookie fallback.
        """

        csrf_token = self._get_cookie_value("csrftoken")
        request_body = urlencode(form_data).encode(
            "utf-8") if form_data else None

        request = Request(
            url,
            data=request_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
                if form_data
                else "application/json",
                "Referer": referer,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "X-ASBD-ID": "198387",
                "X-IG-App-ID": "936619743392459",
                "X-CSRFToken": csrf_token or "",
                "X-Requested-With": "XMLHttpRequest",
            },
            method="POST" if form_data else "GET",
        )

        try:
            opener = self._build_cookie_opener() if use_cookies else None

            if opener:
                _debug_log(
                    "[instagram] Instagram API request using browser cookies "
                    "source=%s",
                    self.settings.ytdlp_cookies_from_browser,
                )
                response_context = opener.open(request, timeout=10)
            else:
                response_context = urlopen(request, timeout=10)

            with response_context as response:
                payload_text = response.read().decode("utf-8")
                _debug_log(
                    "[instagram] Instagram API response url=%s status=%s bytes=%s",
                    url,
                    getattr(response, "status", "unknown"),
                    len(payload_text),
                )
                return json.loads(payload_text)
        except HTTPError as exc:
            body_preview = ""

            try:
                body_preview = exc.read().decode("utf-8")[:800]
            except Exception:
                body_preview = "<unreadable>"

            _debug_log(
                "[instagram] Instagram API request failed url=%s status=%s body=%s",
                url,
                exc.code,
                body_preview,
            )
            if use_cookies and exc.code in {401, 403, 429}:
                _debug_log(
                    "[instagram] retrying Instagram API request without browser cookies "
                    "url=%s status=%s",
                    url,
                    exc.code,
                )
                return self._fetch_instagram_json(
                    url=url,
                    referer=referer,
                    form_data=form_data,
                    use_cookies=False,
                )
            return None
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            _debug_log(
                "[instagram] Instagram API request failed url=%s error=%s", url, exc)
            return None

    def _build_cookie_opener(self):
        """
        Build a urllib opener backed by extracted browser cookies.
        """

        cookie_jar = self._get_browser_cookie_jar()

        if not cookie_jar:
            return None

        return build_opener(HTTPCookieProcessor(cookie_jar))

    def _get_browser_cookie_jar(self):
        """
        Lazily load and cache browser cookies configured for yt-dlp.
        """

        browser_name = self.settings.ytdlp_cookies_from_browser

        if not browser_name:
            return None

        if self._browser_cookie_jar is not None:
            return self._browser_cookie_jar

        try:
            self._browser_cookie_jar = extract_cookies_from_browser(
                browser_name)
            return self._browser_cookie_jar
        except Exception as exc:
            _debug_log(
                "[instagram] could not load browser cookies source=%s error=%s",
                browser_name,
                exc,
            )
            return None

    def _get_cookie_value(self, cookie_name: str) -> str | None:
        """
        Read a named Instagram cookie from the cached browser cookie jar.
        """

        cookie_jar = self._get_browser_cookie_jar()

        if not cookie_jar:
            return None

        for cookie in cookie_jar:
            if cookie.name == cookie_name and "instagram.com" in cookie.domain:
                return cookie.value

        return None

    def _extract_profile_user_id(self, profile_data: Dict[str, Any]) -> str | None:
        """
        Extract Instagram's internal user ID from profile-like API payloads.
        """

        user = self._extract_profile_user_object(profile_data)

        if not isinstance(user, dict):
            return None

        return str(user.get("id") or user.get("pk") or "") or None

    def _extract_clips_next_max_id(
        self,
        clips_data: Dict[str, Any],
    ) -> str | None:
        """
        Extract the pagination cursor for the next clips feed request.
        """

        if not isinstance(clips_data, dict):
            return None

        paging_info = clips_data.get("paging_info")

        if not isinstance(paging_info, dict):
            return None

        more_available = paging_info.get("more_available")
        next_max_id = (
            paging_info.get("max_id")
            or paging_info.get("next_max_id")
            or paging_info.get("next_max_id_str")
            or paging_info.get("next_min_id")
            or paging_info.get("max_id_str")
            or paging_info.get("end_cursor")
            or paging_info.get("cursor")
        )

        if more_available is False:
            return None

        return str(next_max_id) if next_max_id else None

    def _extract_profile_follower_count(
        self,
        profile_data: Dict[str, Any],
    ) -> int | None:
        """
        Extract follower count from an Instagram profile or user payload.
        """

        user = self._extract_profile_user_object(profile_data)

        if not isinstance(user, dict):
            return None

        follower_count = (
            self._count_value(user.get("edge_followed_by"))
            or safe_int(user.get("follower_count"))
            or safe_int(user.get("followers_count"))
        )

        _debug_log(
            "[instagram] creator profile follower count username=%s followers=%s",
            user.get("username"),
            follower_count,
        )

        return follower_count

    def _extract_profile_user_object(
        self,
        profile_data: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """
        Locate the user object across Instagram profile, media, and user payloads.
        """

        if not isinstance(profile_data, dict):
            return None

        data = profile_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("user"), dict):
            return data["user"]

        if isinstance(profile_data.get("user"), dict):
            return profile_data["user"]

        items = profile_data.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("user"), dict):
                    return item["user"]

        return None

    def _merge_count_result(
        self,
        target: dict[str, int | None],
        source: dict[str, int | None] | None,
    ) -> None:
        """
        Fill missing target counts with available values from another source.
        """

        if not source:
            return

        for key in ("follower_count", "views", "likes", "comments"):
            if target.get(key) is None and source.get(key) is not None:
                target[key] = source[key]

    def _has_any_count(self, counts: dict[str, int | None]) -> bool:
        """
        Return whether any count value was found in a fallback result.
        """

        return any(value is not None for value in counts.values())

    def _extract_followers_from_page_text(self, text: str) -> int | None:
        """
        Parse follower count from public Instagram profile page HTML.
        """

        patterns = (
            r'content="([^"]*?Followers[^"]*?)"',
            r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)',
            r'"follower_count"\s*:\s*(\d+)',
            r'"followers_count"\s*:\s*(\d+)',
        )

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue

            value = match.group(1)
            if value.isdigit():
                return safe_int(value)

            count_match = re.search(
                r"([\d,.]+)\s*([KMB])?\s+Followers",
                value,
                flags=re.IGNORECASE,
            )
            if count_match:
                return self._parse_compact_count(
                    count_match.group(1),
                    count_match.group(2),
                )

        return None

    def _parse_compact_count(
        self,
        number_text: str,
        suffix: str | None,
    ) -> int | None:
        """
        Convert compact social counts such as 12.4K or 1.2M into integers.
        """

        try:
            value = float(number_text.replace(",", ""))
        except ValueError:
            return None

        multiplier = {
            "k": 1_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
        }.get((suffix or "").lower(), 1)

        return int(value * multiplier)

    def _find_matching_shortcode_nodes(
        self,
        value: Any,
        shortcode: str,
    ) -> Iterable[Dict[str, Any]]:
        """
        Recursively yield media nodes whose ID or shortcode matches the target.
        """

        if isinstance(value, dict):
            if self._node_matches_shortcode(value, shortcode):
                yield value

            for child in value.values():
                yield from self._find_matching_shortcode_nodes(child, shortcode)

        if isinstance(value, list):
            for child in value:
                yield from self._find_matching_shortcode_nodes(child, shortcode)

    def _node_matches_shortcode(self, node: Dict[str, Any], shortcode: str) -> bool:
        """
        Check whether a media node matches either the shortcode or numeric media PK.
        """

        candidates = (
            node.get("shortcode"),
            node.get("code"),
            node.get("id"),
            node.get("pk"),
        )

        media_pk = self._shortcode_to_media_pk(shortcode)
        normalized_candidates = {str(candidate)
                                 for candidate in candidates if candidate}

        return shortcode in normalized_candidates or (
            media_pk is not None and media_pk in normalized_candidates
        )

    def _extract_profile_grid_view_count(self, node: Dict[str, Any]) -> int | None:
        """
        The visible bottom-left number on Instagram profile Reel tiles is a
        play counter. Prefer play fields before older video_view_count fields.
        """

        return self._first_int_from_nested_keys(
            node,
            "play_count",
            "video_play_count",
            "ig_play_count",
            "fb_play_count",
            "view_count",
            "video_view_count",
        )

    def _debug_count_candidates(self, value: Any) -> dict[str, int]:
        """
        Collect count-like fields from nested payloads for diagnostics.
        """

        candidate_keys = {
            "play_count",
            "video_play_count",
            "ig_play_count",
            "fb_play_count",
            "view_count",
            "video_view_count",
            "like_count",
            "comment_count",
        }
        candidates: dict[str, int] = {}

        self._collect_count_candidates(value, candidate_keys, candidates)

        return candidates

    def _has_profile_play_count(self, candidates: dict[str, int]) -> bool:
        """
        Return whether a matched media node exposes a profile-grid play count.
        """

        return any(
            key in candidates
            for key in (
                "play_count",
                "video_play_count",
                "ig_play_count",
                "fb_play_count",
            )
        )

    def _log_profile_candidate_nodes(
        self,
        username: str,
        profile_data: Dict[str, Any],
        limit: int = 24,
    ) -> None:
        """
        Log candidate media nodes and their count fields for Instagram debugging.
        """

        candidate_nodes = []

        for node in self._iter_profile_media_nodes(profile_data):
            node_id = node.get("shortcode") or node.get(
                "code") or node.get("id")

            if not node_id:
                continue

            candidate_nodes.append(
                {
                    "id": node_id,
                    "is_video": node.get("is_video"),
                    "product_type": node.get("product_type"),
                    "typename": node.get("__typename"),
                    "counts": self._debug_count_candidates(node),
                }
            )

            if len(candidate_nodes) >= limit:
                break

        _debug_log(
            "[instagram] profile candidate nodes creator=%s total_logged=%s "
            "nodes=%s",
            username,
            len(candidate_nodes),
            candidate_nodes,
        )

    def _log_profile_payload_summary(
        self,
        username: str,
        profile_data: Dict[str, Any],
    ) -> None:
        """
        Log a compact summary of a profile or media payload for diagnostics.
        """

        data = profile_data.get("data") if isinstance(
            profile_data, dict) else None
        user = data.get("user") if isinstance(data, dict) else None

        timeline = {}
        media_edges = None

        if isinstance(user, dict):
            timeline = (
                user.get("edge_owner_to_timeline_media")
                or user.get("edge_felix_video_timeline")
                or user.get("edge_user_to_photos_of_you")
                or {}
            )
            media_edges = timeline.get("edges") if isinstance(
                timeline, dict) else None

        _debug_log(
            "[instagram] profile payload summary creator=%s top_keys=%s "
            "status=%s message=%s data_keys=%s user_keys=%s timeline_keys=%s "
            "edge_count=%s items_count=%s raw_preview=%s",
            username,
            list(profile_data.keys()) if isinstance(
                profile_data, dict) else None,
            profile_data.get("status") if isinstance(
                profile_data, dict) else None,
            profile_data.get("message") if isinstance(
                profile_data, dict) else None,
            list(data.keys()) if isinstance(data, dict) else None,
            list(user.keys())[:40] if isinstance(user, dict) else None,
            list(timeline.keys()) if isinstance(timeline, dict) else None,
            len(media_edges) if isinstance(media_edges, list) else None,
            len(profile_data.get("items", []))
            if isinstance(profile_data, dict) and isinstance(profile_data.get("items"), list)
            else None,
            self._profile_payload_preview(profile_data),
        )

    def _iter_profile_media_nodes(self, value: Any) -> Iterable[Dict[str, Any]]:
        """
        Recursively yield nested values that look like Instagram media nodes.
        """

        if isinstance(value, dict):
            if self._looks_like_media_node(value):
                yield value

            for child in value.values():
                yield from self._iter_profile_media_nodes(child)

        if isinstance(value, list):
            for child in value:
                yield from self._iter_profile_media_nodes(child)

    def _looks_like_media_node(self, node: Dict[str, Any]) -> bool:
        """
        Decide whether a dictionary has the identifiers or markers of media.
        """

        has_media_id = any(node.get(key)
                           for key in ("shortcode", "code", "id", "pk"))
        has_count = bool(self._debug_count_candidates(node))
        has_media_marker = any(
            key in node
            for key in (
                "is_video",
                "product_type",
                "__typename",
                "media_type",
                "clips_metadata",
                "video_view_count",
                "play_count",
                "like_count",
            )
        )

        return has_media_id and (has_count or has_media_marker)

    def _profile_payload_preview(self, profile_data: Dict[str, Any]) -> str:
        """
        Serialize a short payload preview for debug logging.
        """

        try:
            return json.dumps(profile_data, default=str)[:1200]
        except (TypeError, ValueError):
            return "<unserializable>"

    def _shortcode_to_media_pk(self, shortcode: str) -> str | None:
        """
        Convert an Instagram shortcode into its numeric media primary key.
        """

        if not shortcode:
            return None

        # Private/long Instagram IDs may append extra data after the shortcode.
        shortcode = shortcode[:28]
        value = 0

        for character in shortcode:
            index = INSTAGRAM_SHORTCODE_ALPHABET.find(character)

            if index < 0:
                return None

            value = value * len(INSTAGRAM_SHORTCODE_ALPHABET) + index

        return str(value)

    def _collect_count_candidates(
        self,
        value: Any,
        candidate_keys: set[str],
        candidates: dict[str, int],
    ) -> None:
        """
        Recursively collect numeric values for selected count field names.
        """

        if isinstance(value, dict):
            for key, child in value.items():
                if key in candidate_keys:
                    count = self._count_value(child)
                    if count is not None:
                        candidates.setdefault(key, count)

                self._collect_count_candidates(
                    child, candidate_keys, candidates)

        if isinstance(value, list):
            for child in value:
                self._collect_count_candidates(
                    child, candidate_keys, candidates)
