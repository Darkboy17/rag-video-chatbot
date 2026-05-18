import uuid
from pathlib import Path
from shutil import which
import subprocess
from typing import Iterable

import yt_dlp

from app.services.media.ytdlp_options import apply_common_ytdlp_options
from app.utils.url_utils import detect_social_platform


class AudioDownloader:
    """
    Downloads source audio and converts it to mp3 for Whisper transcription.
    """

    def __init__(self, settings):
        self.settings = settings

    def download_mp3(
        self,
        url: str,
        platform: str | None = None,
        keep_source: bool = False,
    ) -> str:
        return self.download_audio(
            url=url,
            platform=platform,
            convert_to_mp3=True,
            keep_source=keep_source,
        )

    def download_media(self, url: str, platform: str | None = None) -> str:
        return self.download_audio(
            url=url,
            platform=platform,
            convert_to_mp3=False,
        )

    def download_audio(
        self,
        url: str,
        platform: str | None = None,
        convert_to_mp3: bool = True,
        keep_source: bool = False,
    ) -> str:
        download_dir = Path(self.settings.download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        platform = platform or detect_social_platform(url)

        output_id = str(uuid.uuid4())
        errors: list[str] = []

        for attempt_number, format_selector in enumerate(
            self._format_selectors(
                convert_to_mp3=convert_to_mp3,
                keep_source=keep_source,
            ),
            start=1,
        ):
            attempt_id = output_id if attempt_number == 1 else f"{output_id}-{attempt_number}"
            output_template = str(download_dir / f"{attempt_id}.%(ext)s")

            base_options = {
                "quiet": True,
                "noprogress": True,
                "format": format_selector,
                "outtmpl": output_template,
                "noplaylist": True,
                "retries": 3,
                "fragment_retries": 3,
                "file_access_retries": 3,
                "continuedl": False,
            }

            ydl_opts = apply_common_ytdlp_options(base_options, self.settings)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)

                downloaded_path = self._resolve_downloaded_path(
                    download_dir=download_dir,
                    output_id=attempt_id,
                    expected_extension=None,
                )

                if not downloaded_path:
                    raise FileNotFoundError(
                        "Audio download finished without a readable output file."
                    )

                if not convert_to_mp3:
                    return str(downloaded_path)

                return str(
                    self._convert_to_mp3(
                        source_path=downloaded_path,
                        output_path=download_dir / f"{output_id}.mp3",
                        keep_source=keep_source,
                    )
                )

            except (yt_dlp.utils.DownloadError, FileNotFoundError) as exc:
                errors.append(f"{format_selector}: {exc}")
                if not keep_source:
                    self._cleanup_attempt_files(download_dir, attempt_id)
                else:
                    self._mark_attempt_files_invalid(download_dir, attempt_id)
                continue

        raise FileNotFoundError(
            "Audio download/conversion failed for every attempted format. "
            "The source media may be blocked, unavailable, malformed, or missing "
            "an audio stream. Attempts: " + " | ".join(errors)
        )

    def _resolve_downloaded_path(
        self,
        download_dir: Path,
        output_id: str,
        expected_extension: str | None,
    ) -> Path | None:
        if expected_extension:
            audio_path = download_dir / f"{output_id}.{expected_extension}"

            if audio_path.exists():
                return audio_path

            return None

        candidates = [
            path
            for path in download_dir.glob(f"{output_id}.*")
            if path.is_file() and not path.name.endswith(".part")
        ]

        if not candidates:
            return None

        return max(candidates, key=lambda path: path.stat().st_mtime)

    def _convert_to_mp3(
        self,
        source_path: Path,
        output_path: Path,
        keep_source: bool = False,
    ) -> Path:
        ffmpeg_path = which("ffmpeg")

        if not ffmpeg_path:
            raise FileNotFoundError(
                "ffmpeg is required to extract audio for transcription but was "
                "not found on PATH."
            )

        if source_path == output_path:
            return source_path

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            "-b:a",
            "128k",
            str(output_path),
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0 or not output_path.exists():
            details = (completed.stderr or completed.stdout or "").strip()
            raise FileNotFoundError(
                "Audio conversion failed. The downloaded file may have no audio "
                f"stream or may be unreadable by ffmpeg. ffmpeg output: {details}"
            )

        if not keep_source:
            try:
                source_path.unlink()
            except OSError:
                pass

        return output_path

    def _cleanup_attempt_files(self, download_dir: Path, output_id: str) -> None:
        for path in download_dir.glob(f"{output_id}.*"):
            try:
                path.unlink()
            except OSError:
                pass

    def _mark_attempt_files_invalid(self, download_dir: Path, output_id: str) -> None:
        for path in download_dir.glob(f"{output_id}.*"):
            if ".invalid" in path.name:
                continue

            invalid_path = path.with_name(f"{path.stem}.invalid{path.suffix}")
            try:
                path.rename(invalid_path)
            except OSError:
                pass

    def _format_selectors(
        self,
        convert_to_mp3: bool,
        keep_source: bool = False,
    ) -> Iterable[str]:
        if convert_to_mp3 and keep_source:
            return (
                "best[ext=mp4][vcodec!=none][acodec!=none]",
                "worst[ext=mp4][vcodec!=none][acodec!=none]",
                "best[vcodec!=none][acodec!=none]",
                "bestaudio/best[acodec!=none]",
            )

        if convert_to_mp3:
            return (
                "bestaudio/best[acodec!=none]",
                "best[ext=mp4][acodec!=none]/best[acodec!=none]",
                "worst[ext=mp4][acodec!=none]/worst[acodec!=none]",
            )

        return ("best[acodec!=none]/bestaudio/best",)
