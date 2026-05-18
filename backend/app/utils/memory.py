import ctypes
import logging
import os
import sys
from ctypes import wintypes


def get_process_rss_bytes() -> int | None:
    """
    Return the current resident memory used by this backend process.

    RSS is the closest portable approximation for "how much RAM is this
    process using right now." The implementation stays dependency-free so the
    logger works even before optional profiling tools are installed.
    """

    psutil_rss_bytes = _get_psutil_rss_bytes()
    if psutil_rss_bytes is not None:
        return psutil_rss_bytes

    if sys.platform == "win32":
        return _get_windows_working_set_bytes()

    return _get_proc_status_rss_bytes()


def log_memory_usage(
    logger: logging.Logger,
    *,
    session_id: str,
    stage: str,
    baseline_bytes: int | None = None,
) -> None:
    """
    Emit a structured memory log line for one session lifecycle stage.
    """

    rss_bytes = get_process_rss_bytes()
    delta_bytes = (
        rss_bytes - baseline_bytes
        if rss_bytes is not None and baseline_bytes is not None
        else None
    )

    logger.info(
        "memory_usage session_id=%s stage=%s rss=%s rss_bytes=%s delta=%s delta_bytes=%s",
        session_id,
        stage,
        format_bytes(rss_bytes),
        rss_bytes,
        format_signed_bytes(delta_bytes),
        delta_bytes,
    )


def format_bytes(value: int | None) -> str:
    """
    Format a byte count for human-readable logs.
    """

    if value is None:
        return "unavailable"

    units = ("B", "KB", "MB", "GB")
    amount = float(value)

    for unit in units:
        if abs(amount) < 1024 or unit == units[-1]:
            return f"{amount:.2f}{unit}"
        amount /= 1024

    return f"{amount:.2f}GB"


def format_signed_bytes(value: int | None) -> str:
    """
    Format a byte delta while preserving whether memory rose or fell.
    """

    if value is None:
        return "unavailable"

    sign = "+" if value >= 0 else "-"
    return f"{sign}{format_bytes(abs(value))}"


def _get_windows_working_set_bytes() -> int | None:
    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(ProcessMemoryCounters)

    try:
        kernel32 = ctypes.WinDLL("kernel32.dll")
        psapi = ctypes.WinDLL("psapi.dll")

        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

        current_process = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            current_process,
            ctypes.byref(counters),
            counters.cb,
        )
    except (AttributeError, OSError):
        return None

    if not ok:
        return None

    return int(counters.WorkingSetSize)


def _get_psutil_rss_bytes() -> int | None:
    try:
        import psutil
    except ImportError:
        return None

    try:
        return int(psutil.Process(os.getpid()).memory_info().rss)
    except (OSError, psutil.Error):
        return None


def _get_proc_status_rss_bytes() -> int | None:
    status_path = "/proc/self/status"

    if not os.path.exists(status_path):
        return None

    try:
        with open(status_path, encoding="utf-8") as status_file:
            for line in status_file:
                if not line.startswith("VmRSS:"):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    return None

                return int(parts[1]) * 1024
    except OSError:
        return None

    return None
