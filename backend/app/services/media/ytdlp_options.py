from shutil import which
from typing import Any


def apply_common_ytdlp_options(options: dict[str, Any], settings: Any) -> dict[str, Any]:
    """
    Add shared yt-dlp options used by metadata and audio extraction.
    """

    if settings.ytdlp_cookies_from_browser:
        options["cookiesfrombrowser"] = (
            settings.ytdlp_cookies_from_browser,
            None,
            None,
            None,
        )

    if settings.ytdlp_no_check_certificate:
        options["nocheckcertificate"] = True

    socket_timeout = settings.ytdlp_socket_timeout
    if socket_timeout and socket_timeout > 0:
        options["socket_timeout"] = socket_timeout

    js_runtimes = _build_js_runtimes(settings)
    if js_runtimes:
        options["js_runtimes"] = js_runtimes

    remote_components = _build_remote_components(settings)
    if remote_components:
        options["remote_components"] = remote_components

    return options


def _build_js_runtimes(settings: Any) -> dict[str, dict[str, str]] | None:
    runtime = (settings.ytdlp_js_runtime or "auto").strip().lower()
    runtime_path = (settings.ytdlp_js_runtime_path or "").strip()

    if runtime in {"", "none", "disabled", "off"}:
        return None

    if runtime != "auto":
        return {runtime: {"path": runtime_path} if runtime_path else {}}

    if runtime_path:
        guessed_runtime = _guess_runtime_from_path(runtime_path)
        return {guessed_runtime: {"path": runtime_path}}

    runtime_candidates = (
        ("deno", "deno"),
        ("node", "node"),
        ("bun", "bun"),
        ("quickjs", "qjs"),
    )

    for runtime_name, executable in runtime_candidates:
        found_path = which(executable)
        if found_path:
            return {runtime_name: {"path": found_path}}

    return None


def _guess_runtime_from_path(path: str) -> str:
    lowered = path.replace("\\", "/").rsplit("/", 1)[-1].lower()

    if lowered.startswith("node"):
        return "node"
    if lowered.startswith("bun"):
        return "bun"
    if lowered.startswith("qjs"):
        return "quickjs"

    return "deno"


def _build_remote_components(settings: Any) -> list[str]:
    configured = settings.ytdlp_remote_components or ""

    return [
        component.strip()
        for component in configured.split(",")
        if component.strip()
    ]
