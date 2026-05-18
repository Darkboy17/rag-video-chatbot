from types import SimpleNamespace
from unittest import TestCase

from app.services.media.ytdlp_options import apply_common_ytdlp_options


class YtDlpOptionsTests(TestCase):
    def test_applies_socket_timeout(self):
        settings = self._settings(ytdlp_socket_timeout=60)

        options = apply_common_ytdlp_options({}, settings)

        self.assertEqual(options["socket_timeout"], 60)

    def test_ignores_blank_socket_timeout(self):
        settings = self._settings(ytdlp_socket_timeout=None)

        options = apply_common_ytdlp_options({}, settings)

        self.assertNotIn("socket_timeout", options)

    def _settings(self, **overrides):
        values = {
            "ytdlp_cookies_from_browser": None,
            "ytdlp_no_check_certificate": False,
            "ytdlp_js_runtime": "none",
            "ytdlp_js_runtime_path": None,
            "ytdlp_remote_components": None,
            "ytdlp_socket_timeout": None,
        }
        values.update(overrides)

        return SimpleNamespace(**values)
