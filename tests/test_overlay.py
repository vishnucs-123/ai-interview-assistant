"""
Test Phase 5: Overlay UI.
Run: python -m tests.test_overlay
A floating window should appear top-right of your screen.
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from frontend.overlay.overlay_window import OverlayWindow


def test_overlay():
    app = QApplication(sys.argv)

    window = OverlayWindow()
    window.show()

    # Simulate answers appearing after 2 seconds
    def demo():
        window.append_transcript("Interviewer: Explain polymorphism in Java.")
        window.show_answer(
            question="Explain polymorphism in Java.",
            answer=(
                "Polymorphism allows objects to take multiple forms.\n\n"
                "• Compile-time: Method overloading\n"
                "• Runtime: Method overriding via inheritance\n\n"
                "Example:\n"
                "  Animal a = new Dog();\n"
                "  a.speak(); // calls Dog's speak()\n\n"
                "Key benefit: Write generic code that works with any subclass."
            ),
            category="Technical"
        )

    QTimer.singleShot(2000, demo)

    print("Overlay window open. Close it or press CTRL+SHIFT+Q to quit.")
    print("Shortcuts: CTRL+SHIFT+A (hide/show) | CTRL+SHIFT+T (transcript)")
    sys.exit(app.exec())


if __name__ == "__main__":
    test_overlay()