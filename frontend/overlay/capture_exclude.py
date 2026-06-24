"""
Windows Screen Capture Exclusion.
Makes the overlay window invisible in all screen captures,
screen shares, and recordings using the Windows native API.

Works on: Zoom, Google Meet, Microsoft Teams, OBS, Windows Snipping Tool.
The window remains fully visible to the user on their own screen.

Requirements: Windows 10 version 2004 (build 19041) or later.
"""

import ctypes
import sys
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Windows API constant
# WDA_EXCLUDEFROMCAPTURE = 0x11
# Makes window invisible in all screen captures
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE               = 0x00000000


def apply_capture_exclusion(hwnd: int) -> bool:
    """
    Apply WDA_EXCLUDEFROMCAPTURE to a window handle.
    Call this AFTER the window is shown — HWND is only
    valid once the window has been rendered.

    Args:
        hwnd: Native Windows window handle (from winId())

    Returns:
        True if successful, False otherwise.
    """
    if sys.platform != "win32":
        logger.warning("capture_exclude only works on Windows — skipping")
        return False

    try:
        result = ctypes.windll.user32.SetWindowDisplayAffinity(
            ctypes.c_ulong(hwnd),
            ctypes.c_ulong(WDA_EXCLUDEFROMCAPTURE)
        )

        if result:
            logger.info(
                f"Capture exclusion applied | hwnd={hwnd} | "
                "overlay is now invisible in screen shares"
            )
        else:
            error = ctypes.get_last_error()
            logger.error(
                f"SetWindowDisplayAffinity failed | "
                f"hwnd={hwnd} | error={error}"
            )

        return bool(result)

    except Exception as e:
        logger.error(f"capture_exclude error: {e}")
        return False


def remove_capture_exclusion(hwnd: int) -> bool:
    """
    Remove capture exclusion — makes window visible in captures again.
    Useful for debugging or if user wants to share the overlay.
    """
    if sys.platform != "win32":
        return False

    try:
        result = ctypes.windll.user32.SetWindowDisplayAffinity(
            ctypes.c_ulong(hwnd),
            ctypes.c_ulong(WDA_NONE)
        )
        logger.info("Capture exclusion removed — overlay visible in screen shares")
        return bool(result)
    except Exception as e:
        logger.error(f"remove_capture_exclusion error: {e}")
        return False


def is_supported() -> bool:
    """
    Check if WDA_EXCLUDEFROMCAPTURE is supported on this Windows version.
    Requires Windows 10 build 19041 or later.
    """
    if sys.platform != "win32":
        return False

    try:
        version = sys.getwindowsversion()
        # Windows 10 build 19041+
        supported = (
            version.major > 10 or
            (version.major == 10 and version.build >= 19041)
        )
        if not supported:
            logger.warning(
                f"Windows build {version.build} detected. "
                "WDA_EXCLUDEFROMCAPTURE requires build 19041+."
            )
        return supported
    except Exception:
        return True