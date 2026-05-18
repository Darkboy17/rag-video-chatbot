import os
from typing import List, Dict, Any

import yt_dlp
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi

from app.core.config import get_settings
from app.services.media.audio_downloader import AudioDownloader
from app.utils.url_utils import detect_social_platform, extract_youtube_video_id


class TranscriptUnavailableError(RuntimeError):
    """Raised when transcript extraction cannot produce text for a video."""

    pass


class TranscriptService:
    """
    Transcript extraction strategy:

    1. For YouTube:
       Try youtube-transcript-api first.
       It is faster and free.

    2. For any platform:
       Fall back to mp3 download/extraction + transcription.

    This keeps the system dynamic and usable across YouTube, Shorts,
    TikTok, Instagram Reels, etc., depending on platform availability.
    """

    def __init__(self):
        self.settings = get_settings()
        self.audio_downloader = AudioDownloader(self.settings)
        self.groq_client = Groq(api_key=self.settings.groq_api_key)

    def get_transcript(
        self,
        url: str,
        platform: str | None = None,
    ) -> List[Dict[str, Any]]:
        platform = platform or detect_social_platform(url)
        youtube_id = extract_youtube_video_id(url)

        if platform == "youtube" and youtube_id:
            transcript = self._try_youtube_transcript(youtube_id)
            if transcript:
                return transcript

        return self._transcribe_downloaded_audio(
            url=url,
            platform=platform,
        )

    def _try_youtube_transcript(self, youtube_id: str) -> List[Dict[str, Any]]:
        try:
            api = YouTubeTranscriptApi()
            fetched = api.fetch(youtube_id, languages=["en"])

            entries: List[Dict[str, Any]] = []

            for item in fetched:
                text = getattr(item, "text", None)
                start = getattr(item, "start", None)
                duration = getattr(item, "duration", None)

                if text is None and isinstance(item, dict):
                    text = item.get("text")
                    start = item.get("start")
                    duration = item.get("duration")

                if text:
                    entries.append(
                        {
                            "text": text,
                            "start": start,
                            "duration": duration,
                            "source": "youtube_transcript_api",
                        }
                    )

            return entries

        except Exception:
            return []

    def _transcribe_downloaded_audio(
        self,
        url: str,
        platform: str,
    ) -> List[Dict[str, Any]]:
        try:
            audio_path = self.audio_downloader.download_mp3(
                url=url,
                platform=platform,
                keep_source=platform == "tiktok",
            )
        except yt_dlp.utils.DownloadError as exc:
            raise TranscriptUnavailableError(
                self._download_error_message(platform=platform, reason=str(exc))
            ) from exc
        except FileNotFoundError as exc:
            raise TranscriptUnavailableError(
                self._download_error_message(platform=platform, reason=str(exc))
            ) from exc

        try:
            return self._transcribe_audio(audio_path)

        except TranscriptUnavailableError:
            raise
        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass

    def _transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        provider = (
            getattr(self.settings, "transcription_provider", "auto") or "auto"
        ).strip().lower()

        if provider == "local":
            return self._transcribe_with_local_whisper(audio_path)

        if provider == "groq":
            return self._transcribe_with_groq(audio_path)

        try:
            return self._transcribe_with_groq(audio_path)
        except TranscriptUnavailableError as groq_exc:
            try:
                return self._transcribe_with_local_whisper(audio_path)
            except TranscriptUnavailableError as local_exc:
                raise TranscriptUnavailableError(
                    "Remote transcription failed before local fallback. "
                    f"Groq error: {groq_exc}. Local error: {local_exc}"
                ) from local_exc

    def _transcribe_with_groq(self, audio_path: str) -> List[Dict[str, Any]]:
        verbose_error: Exception | None = None

        try:
            transcription = self._create_groq_transcription(
                audio_path=audio_path,
                response_format="verbose_json",
            )
            return self._parse_groq_transcription(transcription)
        except Exception as exc:
            verbose_error = exc

        try:
            transcription = self._create_groq_transcription(
                audio_path=audio_path,
                response_format="json",
            )
            return self._parse_groq_transcription(transcription)
        except TranscriptUnavailableError:
            raise
        except Exception as exc:
            raise TranscriptUnavailableError(
                "Groq transcription failed for verbose_json and json responses. "
                f"verbose_json error: {verbose_error}; json error: {exc}"
            ) from exc

    def _create_groq_transcription(self, audio_path: str, response_format: str):
        with open(audio_path, "rb") as audio_file:
            return self.groq_client.audio.transcriptions.create(
                file=audio_file,
                model=self.settings.groq_transcription_model,
                response_format=response_format,
            )

    def _parse_groq_transcription(self, transcription) -> List[Dict[str, Any]]:
        entries = self._extract_groq_segments(transcription)
        if entries:
            return entries

        text = getattr(transcription, "text", None)

        if not text and isinstance(transcription, dict):
            text = transcription.get("text")

        if not text:
            raise TranscriptUnavailableError("Groq transcription returned empty text.")

        return [
            {
                "text": text,
                "start": None,
                "duration": None,
                "source": "groq_whisper",
            }
        ]

    def _extract_groq_segments(self, transcription) -> List[Dict[str, Any]]:
        segments = getattr(transcription, "segments", None)

        if segments is None and isinstance(transcription, dict):
            segments = transcription.get("segments")

        if not segments:
            return []

        entries: List[Dict[str, Any]] = []
        for segment in segments:
            text = self._segment_value(segment, "text")
            if not text:
                continue

            start = self._safe_float(self._segment_value(segment, "start"))
            end = self._safe_float(self._segment_value(segment, "end"))
            duration = None

            if start is not None and end is not None:
                duration = max(0, end - start)

            entries.append(
                {
                    "text": str(text).strip(),
                    "start": start,
                    "duration": duration,
                    "source": "groq_whisper",
                }
            )

        return entries

    def _segment_value(self, segment, key: str):
        value = getattr(segment, key, None)

        if value is None and isinstance(segment, dict):
            value = segment.get(key)

        return value

    def _safe_float(self, value) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _transcribe_with_local_whisper(self, audio_path: str) -> List[Dict[str, Any]]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptUnavailableError(
                "Local transcription fallback requires faster-whisper. "
                "Install backend requirements and try again."
            ) from exc

        model_name = getattr(self.settings, "local_whisper_model", "base") or "base"
        device = getattr(self.settings, "local_whisper_device", "cpu") or "cpu"
        compute_type = (
            getattr(self.settings, "local_whisper_compute_type", "int8") or "int8"
        )

        try:
            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
            )
            entries = self._local_whisper_entries(
                model=model,
                audio_path=audio_path,
                vad_filter=True,
            )

            if not entries:
                entries = self._local_whisper_entries(
                    model=model,
                    audio_path=audio_path,
                    vad_filter=False,
                )

            if not entries:
                raise TranscriptUnavailableError(
                    "Local Whisper transcription returned empty text."
                )

            return entries

        except TranscriptUnavailableError:
            raise
        except Exception as exc:
            raise TranscriptUnavailableError(
                f"Local Whisper transcription failed: {exc}"
            ) from exc

    def _local_whisper_entries(
        self,
        model,
        audio_path: str,
        vad_filter: bool,
    ) -> List[Dict[str, Any]]:
        segments, _ = model.transcribe(
            audio_path,
            vad_filter=vad_filter,
        )

        entries: List[Dict[str, Any]] = []

        for segment in segments:
            text = (getattr(segment, "text", "") or "").strip()
            if not text:
                continue

            start = getattr(segment, "start", None)
            end = getattr(segment, "end", None)
            duration = None

            if start is not None and end is not None:
                duration = max(0, end - start)

            entries.append(
                {
                    "text": text,
                    "start": start,
                    "duration": duration,
                    "source": "faster_whisper",
                }
            )

        return entries

    def _download_error_message(self, platform: str, reason: str) -> str:
        if platform == "tiktok":
            return (
                "Could not download a playable TikTok media file for transcription. "
                "Run the backend through an OS-level VPN or use browser cookies "
                "from a local browser session that can play TikTok. "
                f"Download error: {reason}"
            )

        return (
            "Could not download audio for transcription. If this is a YouTube URL, "
            "make sure yt-dlp is installed with its default extras and that Node, "
            "Deno, Bun, or QuickJS is on PATH. "
            f"Download error: {reason}"
        )
