"""
Floating Overlay Window.
A transparent, always-on-top PyQt6 window that displays
AI-generated interview answers over your video call.

Keyboard Shortcuts:
  CTRL+SHIFT+A  — Toggle show/hide
  CTRL+SHIFT+T  — Toggle transcript panel
  CTRL+SHIFT+M  — Mute (stop listening)
  CTRL+SHIFT+Q  — Quit
"""
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
import sys
from frontend.overlay.capture_exclude import apply_capture_exclusion, is_supported
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QSlider
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QThread, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QShortcut, QKeySequence,
    QPainter, QBrush
)

from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

DARK_BG        = "rgba(15, 15, 20, 220)"
CARD_BG        = "rgba(25, 25, 35, 240)"
ACCENT_GREEN   = "#00FF9C"
ACCENT_BLUE    = "#4FC3F7"
ACCENT_YELLOW  = "#FFD54F"
TEXT_PRIMARY   = "#F0F0F0"
TEXT_SECONDARY = "#9E9E9E"
BORDER_COLOR   = "rgba(255,255,255,0.1)"


# ---------------------------------------------------------------------------
# Category badge colors
# ---------------------------------------------------------------------------

CATEGORY_COLORS = {
    "Technical":     "#4FC3F7",
    "Behavioral":    "#A5D6A7",
    "Coding":        "#FFD54F",
    "System Design": "#CE93D8",
    "HR":            "#F48FB1",
    "General":       "#90A4AE",
}


# ---------------------------------------------------------------------------
# Overlay Window
# ---------------------------------------------------------------------------

class OverlayWindow(QWidget):
    """
    Main floating overlay window.
    Transparent background, always on top, draggable.
    """
    def _open_dashboard(self):
        """Open the analytics dashboard window."""
        from frontend.dashboard.dashboard_window import DashboardWindow
        if not hasattr(self, '_dashboard') or self._dashboard is None:
            self._dashboard = DashboardWindow()
            self._dashboard.closed.connect(
                lambda: setattr(self, '_dashboard', None)
            )
        self._dashboard.show()
        self._dashboard.raise_()
    
    def export_pdf(self, session_data: dict):
        """Export current session as PDF."""
        from backend.utils.pdf_exporter import PDFExporter
        exporter = PDFExporter()
        path = exporter.export(session_data)
        self._set_status(f"PDF saved!", "#00FF9C")
        QTimer.singleShot(3000, lambda: self._set_status("Listening...", "#00FF9C"))
        return path
    
    def showEvent(self, event):
        """
        Called every time the window becomes visible.
        Apply capture exclusion here — HWND is only valid
        after the window is actually shown on screen.
        """
        super().showEvent(event)

        hwnd = int(self.winId())

        if not is_supported():
            logger.warning(
                "Windows version too old for capture exclusion. "
                "Overlay may be visible in screen shares."
            )
            return

        success = apply_capture_exclusion(hwnd)

        if success:
            logger.info("Overlay is invisible in screen shares")
        else:
            logger.error(
                "Failed to apply capture exclusion — "
                "overlay may be visible in screen shares"
            )

    # Signal emitted when mute button is toggled
    mute_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._drag_pos = QPoint()
        self._is_muted = False
        self._opacity = 0.92

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()

        logger.info("OverlayWindow initialized")

    # ------------------------------------------------------------------ #
    # Window setup
    # ------------------------------------------------------------------ #

    def _setup_window(self):
        """Configure window flags for overlay behavior."""
        self.setWindowTitle("AI Interview Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |       # No title bar
            Qt.WindowType.WindowStaysOnTopHint |      # Always on top
            Qt.WindowType.Tool                        # No taskbar entry
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(420, 300)
        self.resize(480, 520)

        # Position: top-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 500, 40)

        self.setWindowOpacity(self._opacity)

    def _setup_ui(self):
        """Build all UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Outer container with rounded corners + border
        container = QFrame()
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QFrame#container {{
                background: {DARK_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 16px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(16, 12, 16, 16)
        container_layout.setSpacing(10)

        # Header
        container_layout.addLayout(self._build_header())

        # Divider
        container_layout.addWidget(self._build_divider())

        # Status bar
        container_layout.addWidget(self._build_status_bar())

        # Question display
        container_layout.addWidget(self._build_question_area())

        # Answer display
        container_layout.addWidget(self._build_answer_area(), stretch=1)

        # Transcript (collapsible)
        self._transcript_frame = self._build_transcript_area()
        container_layout.addWidget(self._transcript_frame)

        # Bottom controls
        container_layout.addLayout(self._build_bottom_controls())

        main_layout.addWidget(container)

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # App icon + title
        title_label = QLabel("🎯  AI Interview Assistant")
        title_label.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 14px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)

        # Opacity slider
        opacity_slider = QSlider(Qt.Orientation.Horizontal)
        opacity_slider.setRange(30, 100)
        opacity_slider.setValue(92)
        opacity_slider.setFixedWidth(80)
        opacity_slider.setToolTip("Adjust opacity")
        opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255,255,255,0.15);
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4FC3F7;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
        """)
        opacity_slider.valueChanged.connect(
            lambda v: self.setWindowOpacity(v / 100)
        )

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.1);
                color: {TEXT_SECONDARY};
                border: none;
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(255,80,80,0.6);
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.hide)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(opacity_slider)
        layout.addSpacing(8)
        layout.addWidget(close_btn)
        return layout

    def _build_divider(self) -> QFrame:
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {BORDER_COLOR};")
        return divider

    def _build_status_bar(self) -> QHBoxLayout:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Listening indicator dot
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(
            f"color: {ACCENT_GREEN}; font-size: 10px;"
        )

        self._status_label = QLabel("Listening...")
        self._status_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px;"
        )

        # Category badge
        self._category_badge = QLabel("—")
        self._category_badge.setStyleSheet(f"""
            background: rgba(79,195,247,0.2);
            color: {ACCENT_BLUE};
            font-size: 11px;
            font-weight: bold;
            padding: 2px 10px;
            border-radius: 10px;
        """)

        layout.addWidget(self._status_dot)
        layout.addSpacing(4)
        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addWidget(self._category_badge)
        return frame

    def _build_question_area(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {CARD_BG};
            border-radius: 10px;
            border: 1px solid {BORDER_COLOR};
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        label = QLabel("QUESTION DETECTED")
        label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; letter-spacing: 1px;"
        )

        self._question_label = QLabel("Waiting for interviewer to speak...")
        self._question_label.setWordWrap(True)
        self._question_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-style: italic;"
        )

        layout.addWidget(label)
        layout.addWidget(self._question_label)
        return frame

    def _build_answer_area(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {CARD_BG};
            border-radius: 10px;
            border: 1px solid {BORDER_COLOR};
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        header = QHBoxLayout()
        label = QLabel("AI ANSWER")
        label.setStyleSheet(
            f"color: {ACCENT_GREEN}; font-size: 10px; "
            f"letter-spacing: 1px; font-weight: bold;"
        )

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,255,156,0.15);
                color: {ACCENT_GREEN};
                border: 1px solid rgba(0,255,156,0.3);
                border-radius: 6px;
                font-size: 11px;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background: rgba(0,255,156,0.3); }}
        """)
        self._copy_btn.clicked.connect(self._copy_answer)

        header.addWidget(label)
        header.addStretch()
        header.addWidget(self._copy_btn)

        self._answer_text = QTextEdit()
        self._answer_text.setReadOnly(True)
        self._answer_text.setPlaceholderText("Answer will appear here...")
        self._answer_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                border: none;
                line-height: 1.5;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255,255,255,0.2);
                border-radius: 2px;
            }}
        """)

        layout.addLayout(header)
        layout.addWidget(self._answer_text)
        return frame

    def _build_transcript_area(self) -> QFrame:
        frame = QFrame()
        frame.setVisible(False)  # Hidden by default
        frame.setStyleSheet(f"""
            background: {CARD_BG};
            border-radius: 10px;
            border: 1px solid {BORDER_COLOR};
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)

        label = QLabel("LIVE TRANSCRIPT")
        label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10px; letter-spacing: 1px;"
        )

        self._transcript_text = QTextEdit()
        self._transcript_text.setReadOnly(True)
        self._transcript_text.setMaximumHeight(100)
        self._transcript_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {TEXT_SECONDARY};
                font-size: 12px;
                border: none;
            }}
        """)

        layout.addWidget(label)
        layout.addWidget(self._transcript_text)
        return frame

    def _build_bottom_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        # Mute button
        self._mute_btn = QPushButton("🎙  Listening")
        self._mute_btn.setFixedHeight(32)
        self._mute_btn.setStyleSheet(self._mute_btn_style(active=True))
        self._mute_btn.clicked.connect(self._toggle_mute)

        # Transcript toggle
        transcript_btn = QPushButton("📝  Transcript")
        transcript_btn.setFixedHeight(32)
        transcript_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.08);
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.15); }}
        """)
        transcript_btn.clicked.connect(self._toggle_transcript)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(32)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ color: white; }}
        """)
        # Dashboard button
        dashboard_btn = QPushButton("📊  Stats")
        dashboard_btn.setFixedHeight(32)
        dashboard_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.08);
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.15); }}
        """)
        dashboard_btn.clicked.connect(self._open_dashboard)
        layout.addWidget(dashboard_btn)

        clear_btn.clicked.connect(self._clear_all)

        layout.addWidget(self._mute_btn, stretch=1)
        layout.addWidget(transcript_btn)
        layout.addWidget(clear_btn)
        return layout

    # ------------------------------------------------------------------ #
    # Shortcuts
    # ------------------------------------------------------------------ #

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Shift+A"), self).activated.connect(
            self._toggle_visibility
        )
        QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(
            self._toggle_transcript
        )
        QShortcut(QKeySequence("Ctrl+Shift+M"), self).activated.connect(
            self._toggle_mute
        )
        QShortcut(QKeySequence("Ctrl+Shift+Q"), self).activated.connect(
            QApplication.quit
        )

    # ------------------------------------------------------------------ #
    # Public API — called by the pipeline
    # ------------------------------------------------------------------ #

    def show_answer(self, question: str, answer: str, category: str = "General"):
        """Display a new question + answer in the overlay."""
        self._question_label.setText(question)
        self._answer_text.setPlainText(answer)

        color = CATEGORY_COLORS.get(category, "#90A4AE")
        self._category_badge.setText(f"  {category}  ")
        self._category_badge.setStyleSheet(f"""
            background: rgba(255,255,255,0.1);
            color: {color};
            font-size: 11px;
            font-weight: bold;
            padding: 2px 10px;
            border-radius: 10px;
        """)

        self._set_status("Answer ready", ACCENT_GREEN)
        logger.info(f"Overlay updated | category={category}")

    def append_transcript(self, text: str):
        """Add a line to the live transcript panel."""
        self._transcript_text.append(text)
        self._transcript_text.ensureCursorVisible()

    def set_listening(self, active: bool):
        """Update the status indicator."""
        if active:
            self._set_status("Listening...", ACCENT_GREEN)
        else:
            self._set_status("Muted", "#FF5252")

    # ------------------------------------------------------------------ #
    # Internal slots
    # ------------------------------------------------------------------ #

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def _toggle_transcript(self):
        self._transcript_frame.setVisible(
            not self._transcript_frame.isVisible()
        )

    def _toggle_mute(self):
        self._is_muted = not self._is_muted
        self._mute_btn.setText(
            "🔇  Muted" if self._is_muted else "🎙  Listening"
        )
        self._mute_btn.setStyleSheet(
            self._mute_btn_style(active=not self._is_muted)
        )
        self.set_listening(not self._is_muted)
        self.mute_toggled.emit(self._is_muted)

    def _copy_answer(self):
        text = self._answer_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self._copy_btn.setText("Copied!")
            QTimer.singleShot(2000, lambda: self._copy_btn.setText("Copy"))

    def _clear_all(self):
        self._question_label.setText("Waiting for interviewer to speak...")
        self._answer_text.clear()
        self._transcript_text.clear()
        self._category_badge.setText("—")
        self._set_status("Listening...", ACCENT_GREEN)

    def _set_status(self, text: str, color: str):
        self._status_label.setText(text)
        self._status_dot.setStyleSheet(
            f"color: {color}; font-size: 10px;"
        )

    def _mute_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: rgba(0,255,156,0.15);
                    color: {ACCENT_GREEN};
                    border: 1px solid rgba(0,255,156,0.4);
                    border-radius: 8px;
                    font-size: 12px;
                    padding: 0 14px;
                }}
                QPushButton:hover {{ background: rgba(0,255,156,0.25); }}
            """
        else:
            return f"""
                QPushButton {{
                    background: rgba(255,82,82,0.15);
                    color: #FF5252;
                    border: 1px solid rgba(255,82,82,0.4);
                    border-radius: 8px;
                    font-size: 12px;
                    padding: 0 14px;
                }}
                QPushButton:hover {{ background: rgba(255,82,82,0.25); }}
            """

    # ------------------------------------------------------------------ #
    # Dragging support
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)