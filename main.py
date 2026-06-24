"""
AI Interview Assistant — Main Entry Point.
Run: python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from frontend.overlay.overlay_window import OverlayWindow
from backend.pipeline import Pipeline
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 60)
    print("   AI Interview Assistant")
    print("   Phases complete: Audio → Transcribe → Detect → Answer → UI")
    print("=" * 60)
    print()
    print("Starting... (Whisper model loads in ~10 seconds)")
    print()
    print("Shortcuts:")
    print("  CTRL+SHIFT+A — Hide/Show overlay")
    print("  CTRL+SHIFT+T — Toggle transcript")
    print("  CTRL+SHIFT+M — Mute mic")
    print("  CTRL+SHIFT+Q — Quit")
    print()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create overlay
    overlay = OverlayWindow()
    overlay.show()

    # Create pipeline
    pipeline = Pipeline(
        whisper_model="base",
        ollama_model="llama3.2"
    )

    # Connect pipeline signals to overlay
    pipeline.answer_ready.connect(overlay.show_answer)
    pipeline.transcript_update.connect(overlay.append_transcript)
    pipeline.status_update.connect(
        lambda msg: overlay._set_status(msg, "#4FC3F7")
    )

    # Connect mute button to pipeline
    overlay.mute_toggled.connect(pipeline.set_muted)

    # Start pipeline after UI is shown (500ms delay)
    QTimer.singleShot(500, pipeline.start)

    logger.info("Application started")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()