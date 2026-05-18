import re
from urllib.parse import urlparse, parse_qs


YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com",
                   "m.youtube.com", "youtu.be", "www.youtu.be"}
TIKTOK_DOMAINS = {"tiktok.com", "www.tiktok.com",
                  "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
INSTAGRAM_DOMAINS = {"instagram.com", "www.instagram.com", "m.instagram.com"}


def detect_social_platform(url: str) -> str:
    """
    Classify a source URL before choosing an extractor.

    The backend supports explicit platform services for YouTube, TikTok, and
    Instagram because each source exposes different metadata fields and has
    different blocking behavior.
    """

    hostname = (urlparse(url).hostname or "").lower()

    if hostname in YOUTUBE_DOMAINS or hostname.endswith(".youtube.com"):
        return "youtube"

    if hostname in TIKTOK_DOMAINS or hostname.endswith(".tiktok.com"):
        return "tiktok"

    if hostname in INSTAGRAM_DOMAINS or hostname.endswith(".instagram.com"):
        return "instagram"

    return "unknown"


def extract_youtube_video_id(url: str) -> str | None:
    """
    Extracts YouTube video ID from common YouTube URL formats.

    Supported:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """

    parsed = urlparse(url)

    if parsed.netloc in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/") or None

    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        shorts_match = re.match(r"^/shorts/([^/?]+)", parsed.path)
        if shorts_match:
            return shorts_match.group(1)

    return None


def safe_int(value) -> int | None:
    try:
        if value is None:
            return None

        if isinstance(value, str):
            compact_value = _parse_compact_count(value)
            if compact_value is not None:
                return compact_value

        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_compact_count(value: str) -> int | None:
    """
    Parse social-platform counts such as "12,345", "12.4K", or "1.2M".
    """

    cleaned = value.strip().replace(",", "")
    if not cleaned:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*([KMB])?", cleaned, re.IGNORECASE)
    if not match:
        return None

    number = float(match.group(1))
    suffix = (match.group(2) or "").upper()
    multiplier = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000,
    }.get(suffix)

    if multiplier is None:
        return None

    return int(number * multiplier)
