from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from app.services.media.audio_downloader import AudioDownloader


class AudioDownloaderTests(TestCase):
    @patch("app.services.media.audio_downloader.yt_dlp.YoutubeDL")
    @patch("app.services.media.audio_downloader.uuid.uuid4")
    def test_tiktok_transcription_download_uses_os_network_without_proxy(
        self,
        mock_uuid4,
        mock_youtube_dl,
    ):
        mock_uuid4.return_value = "audio-id"
        downloader = AudioDownloader(
            SimpleNamespace(
                download_dir="storage/downloads",
                ytdlp_cookies_from_browser=None,
                ytdlp_no_check_certificate=False,
                ytdlp_js_runtime="none",
                ytdlp_js_runtime_path=None,
                ytdlp_remote_components=None,
                ytdlp_socket_timeout=None,
            )
        )

        with patch("app.services.media.audio_downloader.Path.glob") as mock_glob:
            downloaded_path = Mock()
            downloaded_path.is_file.return_value = True
            downloaded_path.name = "audio-id.mp4"
            downloaded_path.stat.return_value.st_mtime = 1
            mock_glob.return_value = [downloaded_path]

            with patch.object(
                downloader,
                "_convert_to_mp3",
                return_value=Path("storage/downloads/audio-id.mp3"),
            ):
                downloader.download_mp3(
                    "https://www.tiktok.com/@creator/video/123",
                    platform="tiktok",
                )

        ydl_options = mock_youtube_dl.call_args.args[0]

        self.assertNotIn("proxy", ydl_options)

    @patch("app.services.media.audio_downloader.yt_dlp.YoutubeDL")
    @patch("app.services.media.audio_downloader.uuid.uuid4")
    def test_instagram_download_uses_os_network_without_proxy(self, mock_uuid4, mock_youtube_dl):
        mock_uuid4.return_value = "audio-id"
        downloader = AudioDownloader(
            SimpleNamespace(
                download_dir="storage/downloads",
                ytdlp_cookies_from_browser=None,
                ytdlp_no_check_certificate=False,
                ytdlp_js_runtime="none",
                ytdlp_js_runtime_path=None,
                ytdlp_remote_components=None,
                ytdlp_socket_timeout=None,
            )
        )

        with patch("app.services.media.audio_downloader.Path.glob") as mock_glob:
            downloaded_path = Mock()
            downloaded_path.is_file.return_value = True
            downloaded_path.name = "audio-id.mp4"
            downloaded_path.stat.return_value.st_mtime = 1
            mock_glob.return_value = [downloaded_path]

            with patch.object(
                downloader,
                "_convert_to_mp3",
                return_value=Path("storage/downloads/audio-id.mp3"),
            ):
                downloader.download_mp3(
                    "https://www.instagram.com/reel/example/",
                    platform="instagram",
                )

        ydl_options = mock_youtube_dl.call_args.args[0]

        self.assertNotIn("proxy", ydl_options)
        self.assertNotIn("postprocessors", ydl_options)

    @patch("app.services.media.audio_downloader.yt_dlp.YoutubeDL")
    @patch("app.services.media.audio_downloader.uuid.uuid4")
    def test_download_media_skips_ffmpeg_postprocessor(self, mock_uuid4, mock_youtube_dl):
        mock_uuid4.return_value = "audio-id"
        downloader = AudioDownloader(
            SimpleNamespace(
                download_dir="storage/downloads",
                ytdlp_cookies_from_browser=None,
                ytdlp_no_check_certificate=False,
                ytdlp_js_runtime="none",
                ytdlp_js_runtime_path=None,
                ytdlp_remote_components=None,
                ytdlp_socket_timeout=None,
            )
        )

        with patch("app.services.media.audio_downloader.Path.glob") as mock_glob:
            downloaded_path = Mock()
            downloaded_path.is_file.return_value = True
            downloaded_path.name = "audio-id.mp4"
            downloaded_path.stat.return_value.st_mtime = 1
            mock_glob.return_value = [downloaded_path]

            path = downloader.download_media(
                "https://www.tiktok.com/@creator/video/123",
                platform="tiktok",
            )

        ydl_options = mock_youtube_dl.call_args.args[0]

        self.assertEqual(path, str(downloaded_path))
        self.assertNotIn("postprocessors", ydl_options)
        self.assertEqual(ydl_options["format"], "best[acodec!=none]/bestaudio/best")

    @patch("app.services.media.audio_downloader.yt_dlp.YoutubeDL")
    @patch("app.services.media.audio_downloader.uuid.uuid4")
    def test_download_mp3_retries_with_alternate_format_after_bad_media(
        self,
        mock_uuid4,
        mock_youtube_dl,
    ):
        mock_uuid4.return_value = "audio-id"
        downloader = AudioDownloader(
            SimpleNamespace(
                download_dir="storage/downloads",
                ytdlp_cookies_from_browser=None,
                ytdlp_no_check_certificate=False,
                ytdlp_js_runtime="none",
                ytdlp_js_runtime_path=None,
                ytdlp_remote_components=None,
                ytdlp_socket_timeout=None,
            )
        )

        with patch("app.services.media.audio_downloader.Path.glob") as mock_glob:
            first_path = Mock()
            first_path.is_file.return_value = True
            first_path.name = "audio-id.mp4"
            first_path.stat.return_value.st_mtime = 1

            second_path = Mock()
            second_path.is_file.return_value = True
            second_path.name = "audio-id-2.mp4"
            second_path.stat.return_value.st_mtime = 2

            mock_glob.side_effect = [
                [first_path],
                [],
                [second_path],
            ]

            with patch.object(
                downloader,
                "_convert_to_mp3",
                side_effect=[
                    FileNotFoundError("bad media"),
                    Path("storage/downloads/audio-id.mp3"),
                ],
            ):
                path = downloader.download_mp3(
                    "https://www.tiktok.com/@creator/video/123",
                    platform="tiktok",
                )

        first_options = mock_youtube_dl.call_args_list[0].args[0]
        second_options = mock_youtube_dl.call_args_list[1].args[0]

        self.assertEqual(path, "storage\\downloads\\audio-id.mp3")
        self.assertEqual(first_options["format"], "bestaudio/best[acodec!=none]")
        self.assertEqual(
            second_options["format"],
            "best[ext=mp4][acodec!=none]/best[acodec!=none]",
        )

    def test_keep_source_prefers_playable_mp4_video_formats(self):
        downloader = AudioDownloader(SimpleNamespace(download_dir="storage/downloads"))

        selectors = list(
            downloader._format_selectors(
                convert_to_mp3=True,
                keep_source=True,
            )
        )

        self.assertEqual(
            selectors[0],
            "best[ext=mp4][vcodec!=none][acodec!=none]",
        )
        self.assertEqual(
            selectors[1],
            "worst[ext=mp4][vcodec!=none][acodec!=none]",
        )

    @patch("app.services.media.audio_downloader.yt_dlp.YoutubeDL")
    @patch("app.services.media.audio_downloader.uuid.uuid4")
    def test_download_mp3_can_keep_downloaded_source_file(
        self,
        mock_uuid4,
        mock_youtube_dl,
    ):
        mock_uuid4.return_value = "audio-id"
        downloader = AudioDownloader(
            SimpleNamespace(
                download_dir="storage/downloads",
                ytdlp_cookies_from_browser=None,
                ytdlp_no_check_certificate=False,
                ytdlp_js_runtime="none",
                ytdlp_js_runtime_path=None,
                ytdlp_remote_components=None,
                ytdlp_socket_timeout=None,
            )
        )

        with patch("app.services.media.audio_downloader.Path.glob") as mock_glob:
            downloaded_path = Mock()
            downloaded_path.is_file.return_value = True
            downloaded_path.name = "audio-id.mp4"
            downloaded_path.stat.return_value.st_mtime = 1
            mock_glob.return_value = [downloaded_path]

            with patch.object(
                downloader,
                "_convert_to_mp3",
                return_value=Path("storage/downloads/audio-id.mp3"),
            ) as mock_convert:
                downloader.download_mp3(
                    "https://www.tiktok.com/@creator/video/123",
                    platform="tiktok",
                    keep_source=True,
                )

        mock_convert.assert_called_once_with(
            source_path=downloaded_path,
            output_path=Path("storage/downloads/audio-id.mp3"),
            keep_source=True,
        )
