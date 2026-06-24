"""
Test Phase 11: Screen-Share Invisibility.
Run: python -m tests.test_capture_exclude

This test:
1. Opens the overlay window
2. Applies WDA_EXCLUDEFROMCAPTURE
3. Shows a verification message

To manually verify:
- Open Zoom or Google Meet
- Start screen share (share entire screen)
- The overlay should be INVISIBLE in the shared view
- But fully visible on your own monitor
"""

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from frontend.overlay.overlay_window import OverlayWindow
from frontend.overlay.capture_exclude import (
    apply_capture_exclusion,
    remove_capture_exclusion,
    is_supported
)


def test_capture_exclude():
    print("=== Phase 11: Screen-Share Invisibility Test ===\n")

    if not is_supported():
        print("WARNING: Your Windows version may not support this feature.")
        print("Requires Windows 10 build 19041 or later.")
    else:
        print("Windows version: SUPPORTED")

    app = QApplication(sys.argv)

    overlay = OverlayWindow()

    # Pre-fill with test message
    overlay.show_answer(
        question="Can the interviewer see this overlay?",
        answer=(
            "NO — this overlay is invisible in screen shares.\n\n"
            "- Zoom: invisible\n"
            "- Google Meet: invisible\n"
            "- Microsoft Teams: invisible\n"
            "- OBS capture: invisible\n\n"
            "Only YOU can see this window."
        ),
        category="Technical"
    )

    overlay.show()

    # showEvent applies capture exclusion automatically
    # Verify it was applied
    def verify():
        hwnd = int(overlay.winId())
        print(f"Window handle (HWND): {hwnd}")
        print()
        print("Overlay is now open.")
        print()
        print("To verify invisibility:")
        print("1. Open Zoom / Google Meet / Teams")
        print("2. Start screen share (share ENTIRE screen)")
        print("3. Look at the shared view on another device")
        print("   → The overlay should NOT appear in the share")
        print("   → But it IS visible on your screen right now")
        print()
        print("Shortcuts: CTRL+SHIFT+A (hide/show) | CTRL+SHIFT+Q (quit)")

    QTimer.singleShot(500, verify)

    sys.exit(app.exec())


if __name__ == "__main__":
    test_capture_exclude()