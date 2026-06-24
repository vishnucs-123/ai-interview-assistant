"""
Interview Analytics Dashboard.
A separate PyQt6 window showing real-time interview statistics:
- Total questions answered
- Category breakdown (pie chart)
- Top topics (bar chart)
- Recent Q&A history list
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

DARK_BG      = "#0F0F14"
CARD_BG      = "#19191F"
BORDER       = "#2A2A35"
TEXT_PRIMARY = "#F0F0F0"
TEXT_MUTED   = "#9E9E9E"

CATEGORY_COLORS = {
    "Technical":     "#4FC3F7",
    "Behavioral":    "#A5D6A7",
    "Coding":        "#FFD54F",
    "System Design": "#CE93D8",
    "HR":            "#F48FB1",
    "General":       "#90A4AE",
}


# ---------------------------------------------------------------------------
# Reusable stat card widget
# ---------------------------------------------------------------------------

class StatCard(QFrame):
    """A single metric card showing a number and label."""

    def __init__(self, title: str, value: str, color: str = "#4FC3F7"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: bold; border: none;"
        )

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; border: none;"
        )

        layout.addWidget(self._value_label)
        layout.addWidget(title_label)

    def update_value(self, value: str):
        self._value_label.setText(value)


# ---------------------------------------------------------------------------
# Matplotlib chart canvas
# ---------------------------------------------------------------------------

class ChartCanvas(FigureCanvasQTAgg):
    """Embeds a matplotlib figure into PyQt6."""

    def __init__(self, width=4, height=3):
        self.fig = Figure(
            figsize=(width, height),
            facecolor=CARD_BG,
            tight_layout=True
        )
        super().__init__(self.fig)
        self.setStyleSheet(f"background: {CARD_BG}; border-radius: 12px;")


# ---------------------------------------------------------------------------
# Main Dashboard Window
# ---------------------------------------------------------------------------

class DashboardWindow(QWidget):
    """
    Analytics dashboard — shows interview statistics.
    Opens as a separate window from the overlay.
    """

    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._history: list[dict] = []
        self._setup_window()
        self._setup_ui()
        logger.info("DashboardWindow initialized")

    def _setup_window(self):
        self.setWindowTitle("Interview Analytics")
        self.resize(860, 640)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"background: {DARK_BG}; color: {TEXT_PRIMARY};")

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        # Header
        main.addLayout(self._build_header())

        # Stat cards row
        main.addLayout(self._build_stat_cards())

        # Charts row
        main.addLayout(self._build_charts_row(), stretch=1)

        # Recent Q&A list
        main.addWidget(self._build_history_panel(), stretch=1)

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        title = QLabel("📊  Interview Analytics")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: bold;"
        )

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(30)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.08);
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; }}
        """)
        refresh_btn.clicked.connect(self._refresh_charts)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(refresh_btn)
        return layout

    def _build_stat_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self._card_total     = StatCard("Total Questions", "0", "#4FC3F7")
        self._card_technical = StatCard("Technical",       "0", "#4FC3F7")
        self._card_behavioral= StatCard("Behavioral",      "0", "#A5D6A7")
        self._card_coding    = StatCard("Coding",          "0", "#FFD54F")

        for card in [
            self._card_total,
            self._card_technical,
            self._card_behavioral,
            self._card_coding
        ]:
            layout.addWidget(card)

        return layout

    def _build_charts_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Pie chart — category breakdown
        pie_frame = QFrame()
        pie_frame.setStyleSheet(f"""
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
        """)
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(12, 10, 12, 10)

        pie_title = QLabel("Category Breakdown")
        pie_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1px;"
        )

        self._pie_canvas = ChartCanvas(width=4, height=3)
        pie_layout.addWidget(pie_title)
        pie_layout.addWidget(self._pie_canvas)

        # Bar chart — top topics
        bar_frame = QFrame()
        bar_frame.setStyleSheet(f"""
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
        """)
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(12, 10, 12, 10)

        bar_title = QLabel("Top Topics")
        bar_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1px;"
        )

        self._bar_canvas = ChartCanvas(width=4, height=3)
        bar_layout.addWidget(bar_title)
        bar_layout.addWidget(self._bar_canvas)

        layout.addWidget(pie_frame)
        layout.addWidget(bar_frame)
        return layout

    def _build_history_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {CARD_BG};
            border: 1px solid {BORDER};
            border-radius: 12px;
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        header_label = QLabel("Recent Questions")
        header_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; letter-spacing: 1px;"
        )
        layout.addWidget(header_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.15); border-radius: 2px;
            }
        """)

        self._history_container = QWidget()
        self._history_container.setStyleSheet("background: transparent;")
        self._history_layout = QVBoxLayout(self._history_container)
        self._history_layout.setSpacing(6)
        self._history_layout.addStretch()

        scroll.setWidget(self._history_container)
        layout.addWidget(scroll)
        return frame

    # ------------------------------------------------------------------ #
    # Public API — called by pipeline or main window
    # ------------------------------------------------------------------ #

    def update_data(self, summary: dict, history: list[dict]):
        """
        Refresh dashboard with new data.

        summary: dict from ConversationMemory.get_summary()
        history: list of {question, answer, category, topic} dicts
        """
        self._history = history
        self._update_stat_cards(summary)
        self._draw_pie_chart(summary.get("categories", {}))
        self._draw_bar_chart(history)
        self._update_history_list(history)
        logger.info("Dashboard updated")

    # ------------------------------------------------------------------ #
    # Internal update methods
    # ------------------------------------------------------------------ #

    def _update_stat_cards(self, summary: dict):
        categories = summary.get("categories", {})
        self._card_total.update_value(str(summary.get("total_questions", 0)))
        self._card_technical.update_value(str(categories.get("Technical", 0)))
        self._card_behavioral.update_value(str(categories.get("Behavioral", 0)))
        self._card_coding.update_value(str(categories.get("Coding", 0)))

    def _draw_pie_chart(self, categories: dict):
        self._pie_canvas.fig.clear()

        if not categories:
            ax = self._pie_canvas.fig.add_subplot(111)
            ax.set_facecolor(CARD_BG)
            ax.text(
                0.5, 0.5, "No data yet",
                ha="center", va="center",
                color=TEXT_MUTED, fontsize=12,
                transform=ax.transAxes
            )
            ax.axis("off")
            self._pie_canvas.draw()
            return

        labels = list(categories.keys())
        sizes  = list(categories.values())
        colors = [CATEGORY_COLORS.get(l, "#90A4AE") for l in labels]

        ax = self._pie_canvas.fig.add_subplot(111)
        ax.set_facecolor(CARD_BG)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=140,
            pctdistance=0.75,
            wedgeprops={"linewidth": 1.5, "edgecolor": DARK_BG}
        )

        for t in texts:
            t.set_color(TEXT_MUTED)
            t.set_fontsize(9)
        for at in autotexts:
            at.set_color(TEXT_PRIMARY)
            at.set_fontsize(9)
            at.set_fontweight("bold")

        self._pie_canvas.draw()

    def _draw_bar_chart(self, history: list[dict]):
        self._bar_canvas.fig.clear()

        if not history:
            ax = self._bar_canvas.fig.add_subplot(111)
            ax.set_facecolor(CARD_BG)
            ax.text(
                0.5, 0.5, "No data yet",
                ha="center", va="center",
                color=TEXT_MUTED, fontsize=12,
                transform=ax.transAxes
            )
            ax.axis("off")
            self._bar_canvas.draw()
            return

        # Count topics
        topic_counts: dict[str, int] = {}
        for entry in history:
            topic = entry.get("topic", "General")
            if topic != "General":
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        if not topic_counts:
            topic_counts = {"General": len(history)}

        # Top 6 topics
        sorted_topics = sorted(
            topic_counts.items(), key=lambda x: x[1], reverse=True
        )[:6]
        topics = [t[0] for t in sorted_topics]
        counts = [t[1] for t in sorted_topics]
        colors = [CATEGORY_COLORS.get(t, "#4FC3F7") for t in topics]

        ax = self._bar_canvas.fig.add_subplot(111)
        ax.set_facecolor(CARD_BG)
        self._bar_canvas.fig.patch.set_facecolor(CARD_BG)

        bars = ax.barh(topics, counts, color=colors, height=0.5)

        for bar, count in zip(bars, counts):
            ax.text(
                bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center", ha="left",
                color=TEXT_PRIMARY, fontsize=9
            )

        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        ax.spines[:].set_visible(False)
        ax.set_xlim(0, max(counts) + 1.5)
        ax.xaxis.set_visible(False)
        ax.invert_yaxis()

        self._bar_canvas.draw()

    def _update_history_list(self, history: list[dict]):
        # Clear existing items (keep the stretch at end)
        while self._history_layout.count() > 1:
            item = self._history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add most recent first
        for entry in reversed(history[-10:]):
            row = self._build_history_row(entry)
            self._history_layout.insertWidget(0, row)

    def _build_history_row(self, entry: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.04);
                border-radius: 8px;
                border: 1px solid {BORDER};
            }}
        """)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        category = entry.get("category", "General")
        color = CATEGORY_COLORS.get(category, "#90A4AE")

        badge = QLabel(category)
        badge.setFixedWidth(90)
        badge.setStyleSheet(f"""
            background: rgba(255,255,255,0.08);
            color: {color};
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 8px;
            border: none;
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        question = QLabel(entry.get("question", "")[:80] + "...")
        question.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; border: none;"
        )
        question.setWordWrap(False)

        layout.addWidget(badge)
        layout.addWidget(question, stretch=1)
        return row

    def _refresh_charts(self):
        """Re-draw charts with current data."""
        if self._history:
            from collections import Counter
            cats = Counter(e.get("category", "General") for e in self._history)
            self._draw_pie_chart(dict(cats))
            self._draw_bar_chart(self._history)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)