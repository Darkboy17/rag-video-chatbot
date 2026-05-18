from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from app.services.transcripts.service import TranscriptService, TranscriptUnavailableError


class TranscriptServiceTests(TestCase):
    def test_tiktok_downloads_mp3_and_transcribes_with_groq(self):
        service = self._service()
        service.audio_downloader.download_mp3.return_value = "fake.mp3"
        service._transcribe_with_groq = Mock(return_value=[{"text": "groq"}])

        transcript = service._transcribe_downloaded_audio(
            url="https://www.tiktok.com/@creator/video/123",
            platform="tiktok",
        )

        self.assertEqual(transcript, [{"text": "groq"}])
        service.audio_downloader.download_mp3.assert_called_once_with(
            url="https://www.tiktok.com/@creator/video/123",
            platform="tiktok",
            keep_source=True,
        )
        service.audio_downloader.download_media.assert_not_called()
        service._transcribe_with_groq.assert_called_once_with("fake.mp3")

    def test_non_tiktok_downloads_mp3_and_transcribes_with_groq(self):
        service = self._service()
        service.audio_downloader.download_mp3.return_value = "fake.mp3"
        service._transcribe_with_groq = Mock(return_value=[{"text": "groq"}])

        transcript = service._transcribe_downloaded_audio(
            url="https://www.instagram.com/reel/example/",
            platform="instagram",
        )

        self.assertEqual(transcript, [{"text": "groq"}])
        service.audio_downloader.download_mp3.assert_called_once_with(
            url="https://www.instagram.com/reel/example/",
            platform="instagram",
            keep_source=False,
        )
        service.audio_downloader.download_media.assert_not_called()
        service._transcribe_with_groq.assert_called_once_with("fake.mp3")

    def test_auto_transcription_falls_back_to_local_when_groq_fails(self):
        service = self._service()
        service._transcribe_with_groq = Mock(
            side_effect=TranscriptUnavailableError("forbidden")
        )
        service._transcribe_with_local_whisper = Mock(return_value=[{"text": "local"}])

        transcript = service._transcribe_audio("fake.mp3")

        self.assertEqual(transcript, [{"text": "local"}])
        service._transcribe_with_groq.assert_called_once_with("fake.mp3")
        service._transcribe_with_local_whisper.assert_called_once_with("fake.mp3")

    def test_local_transcription_provider_skips_groq(self):
        service = self._service()
        service.settings.transcription_provider = "local"
        service._transcribe_with_groq = Mock(return_value=[{"text": "groq"}])
        service._transcribe_with_local_whisper = Mock(return_value=[{"text": "local"}])

        transcript = service._transcribe_audio("fake.mp3")

        self.assertEqual(transcript, [{"text": "local"}])
        service._transcribe_with_groq.assert_not_called()
        service._transcribe_with_local_whisper.assert_called_once_with("fake.mp3")

    def test_youtube_transcript_api_still_runs_before_download(self):
        service = self._service()
        service._try_youtube_transcript = Mock(return_value=[{"text": "youtube"}])
        service._transcribe_downloaded_audio = Mock(return_value=[{"text": "groq"}])

        transcript = service.get_transcript(
            url="https://www.youtube.com/watch?v=abc123",
            platform="youtube",
        )

        self.assertEqual(transcript, [{"text": "youtube"}])
        service._try_youtube_transcript.assert_called_once_with("abc123")
        service._transcribe_downloaded_audio.assert_not_called()

    def test_extracts_timestamped_groq_segments(self):
        service = self._service()

        entries = service._extract_groq_segments(
            {
                "segments": [
                    {"text": "opening line", "start": "0.0", "end": "3.25"},
                    {"text": "next line", "start": 3.25, "end": 6.0},
                ]
            }
        )

        self.assertEqual(
            entries,
            [
                {
                    "text": "opening line",
                    "start": 0.0,
                    "duration": 3.25,
                    "source": "groq_whisper",
                },
                {
                    "text": "next line",
                    "start": 3.25,
                    "duration": 2.75,
                    "source": "groq_whisper",
                },
            ],
        )

    def test_groq_falls_back_to_plain_json_when_verbose_json_fails(self):
        service = self._service()
        service._create_groq_transcription = Mock(
            side_effect=[
                RuntimeError("verbose_json unsupported"),
                {"text": "plain transcript"},
            ]
        )

        transcript = service._transcribe_with_groq("fake.mp3")

        self.assertEqual(
            transcript,
            [
                {
                    "text": "plain transcript",
                    "start": None,
                    "duration": None,
                    "source": "groq_whisper",
                }
            ],
        )
        self.assertEqual(service._create_groq_transcription.call_count, 2)

    def _service(self):
        service = TranscriptService.__new__(TranscriptService)
        service.settings = SimpleNamespace(
            transcription_provider="auto",
            local_whisper_model="base",
            local_whisper_device="cpu",
            local_whisper_compute_type="int8",
        )
        service.audio_downloader = SimpleNamespace(
            download_media=Mock(),
            download_mp3=Mock(),
        )

        return service
