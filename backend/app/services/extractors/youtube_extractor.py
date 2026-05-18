from app.services.extractors.base import BaseYtDlpVideoExtractor


class YouTubeVideoExtractor(BaseYtDlpVideoExtractor):
    """
    Extracts metadata for YouTube videos and Shorts.

    YouTube is the best-supported path because we can combine yt-dlp metadata
    with youtube-transcript-api before falling back to Whisper transcription.
    """

    platform_name = "youtube"
    blocked_reason = (
        "YouTube metadata extraction failed. YouTube may require browser "
        "cookies or a supported JavaScript runtime for challenge solving."
    )
