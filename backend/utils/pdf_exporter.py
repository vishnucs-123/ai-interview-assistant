"""
PDF Report Generator.
Exports a complete interview session as a PDF:
- Header with date and duration
- Analytics summary
- Full Q&A transcript with categories
- Topic breakdown
Uses ReportLab for fully offline PDF generation.
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from backend.utils.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

C_DARK       = colors.HexColor("#0F0F14")
C_CARD       = colors.HexColor("#19191F")
C_ACCENT     = colors.HexColor("#4FC3F7")
C_GREEN      = colors.HexColor("#00FF9C")
C_YELLOW     = colors.HexColor("#FFD54F")
C_PURPLE     = colors.HexColor("#CE93D8")
C_PINK       = colors.HexColor("#F48FB1")
C_SAGE       = colors.HexColor("#A5D6A7")
C_GRAY       = colors.HexColor("#9E9E9E")
C_WHITE      = colors.white
C_BG         = colors.HexColor("#F8F9FA")
C_TEXT       = colors.HexColor("#1A1A2E")
C_MUTED      = colors.HexColor("#6C6C80")
C_BORDER     = colors.HexColor("#E0E0E8")

CATEGORY_COLORS = {
    "Technical":     colors.HexColor("#1565C0"),
    "Behavioral":    colors.HexColor("#2E7D32"),
    "Coding":        colors.HexColor("#E65100"),
    "System Design": colors.HexColor("#6A1B9A"),
    "HR":            colors.HexColor("#880E4F"),
    "General":       colors.HexColor("#37474F"),
}


# ---------------------------------------------------------------------------
# PDF Exporter
# ---------------------------------------------------------------------------

class PDFExporter:
    """
    Generates a professional interview report PDF.

    Usage:
        exporter = PDFExporter()
        path = exporter.export(session_data)
        print(f"Saved to: {path}")
    """

    def __init__(self):
        REPORTS_DIR.mkdir(exist_ok=True)
        self._styles = self._build_styles()
        logger.info("PDFExporter initialized")

    def export(self, session_data: dict) -> str:
        """
        Generate PDF report from session data.

        session_data keys:
            started_at: str
            ended_at: str (optional)
            summary: dict  (from ConversationMemory.get_summary())
            history: list of {question, answer, category, topic, time}

        Returns path to generated PDF.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.pdf"
        output_path = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        story = []

        # Build sections
        story += self._build_header(session_data)
        story += self._build_summary_section(session_data.get("summary", {}))
        story += self._build_qa_section(session_data.get("history", []))
        story += self._build_footer()

        doc.build(story)

        logger.info(f"PDF exported: {output_path}")
        print(f"\nReport saved: {output_path}")
        return str(output_path)

    # ------------------------------------------------------------------ #
    # Section builders
    # ------------------------------------------------------------------ #

    def _build_header(self, session_data: dict) -> list:
        story = []

        # App title bar
        title_data = [["🎯  AI Interview Assistant — Session Report"]]
        title_table = Table(title_data, colWidths=[170*mm])
        title_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,-1), C_DARK),
            ("TEXTCOLOR",   (0,0), (-1,-1), C_ACCENT),
            ("FONTNAME",    (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 16),
            ("TOPPADDING",  (0,0), (-1,-1), 12),
            ("BOTTOMPADDING",(0,0),(-1,-1), 12),
            ("LEFTPADDING", (0,0), (-1,-1), 14),
            ("ROUNDEDCORNERS", [6]),
        ]))
        story.append(title_table)
        story.append(Spacer(1, 8*mm))

        # Meta info row
        started = session_data.get("started_at", "—")
        ended   = session_data.get("ended_at", "—")
        total_q = session_data.get("summary", {}).get("total_questions", 0)

        meta_data = [[
            f"Date: {started[:10] if started != '—' else '—'}",
            f"Start: {started[11:19] if len(started) > 10 else '—'}",
            f"End: {ended[11:19] if len(ended) > 10 else '—'}",
            f"Questions: {total_q}",
        ]]
        meta_table = Table(meta_data, colWidths=[42*mm]*4)
        meta_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), C_BG),
            ("TEXTCOLOR",    (0,0), (-1,-1), C_MUTED),
            ("FONTNAME",     (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("ALIGN",        (0,0), (-1,-1), "CENTER"),
            ("TOPPADDING",   (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
            ("BOX",          (0,0), (-1,-1), 0.5, C_BORDER),
            ("INNERGRID",    (0,0), (-1,-1), 0.5, C_BORDER),
            ("ROUNDEDCORNERS", [4]),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8*mm))
        return story

    def _build_summary_section(self, summary: dict) -> list:
        story = []

        story.append(Paragraph("Analytics Summary", self._styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
        story.append(Spacer(1, 4*mm))

        categories = summary.get("categories", {})
        topics = summary.get("topics_covered", [])

        if not categories:
            story.append(Paragraph("No questions recorded.", self._styles["muted"]))
            story.append(Spacer(1, 6*mm))
            return story

        # Category breakdown table
        cat_rows = [["Category", "Count", "Percentage"]]
        total = sum(categories.values()) or 1
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            pct = f"{count/total*100:.0f}%"
            cat_rows.append([cat, str(count), pct])

        cat_table = Table(cat_rows, colWidths=[80*mm, 40*mm, 50*mm])
        cat_table.setStyle(TableStyle([
            # Header row
            ("BACKGROUND",   (0,0), (-1,0), C_DARK),
            ("TEXTCOLOR",    (0,0), (-1,0), C_ACCENT),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,0), 9),
            # Data rows
            ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",     (0,1), (-1,-1), 9),
            ("TEXTCOLOR",    (0,1), (-1,-1), C_TEXT),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_BG]),
            # Grid
            ("BOX",          (0,0), (-1,-1), 0.5, C_BORDER),
            ("INNERGRID",    (0,0), (-1,-1), 0.5, C_BORDER),
            # Padding
            ("TOPPADDING",   (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 6),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 4*mm))

        if topics:
            topics_text = "Topics covered: " + ", ".join(topics)
            story.append(Paragraph(topics_text, self._styles["muted"]))

        story.append(Spacer(1, 8*mm))
        return story

    def _build_qa_section(self, history: list[dict]) -> list:
        story = []

        story.append(Paragraph("Questions & Answers", self._styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
        story.append(Spacer(1, 4*mm))

        if not history:
            story.append(Paragraph("No Q&A recorded.", self._styles["muted"]))
            return story

        for i, entry in enumerate(history, 1):
            category = entry.get("category", "General")
            topic    = entry.get("topic", "")
            question = entry.get("question", "")
            answer   = entry.get("answer", "")
            time_str = entry.get("time", "")

            cat_color = CATEGORY_COLORS.get(category, C_MUTED)

            # Q number + meta row
            meta_text = f"Q{i}  ·  {category}"
            if topic and topic != "General":
                meta_text += f"  ·  {topic}"
            if time_str:
                meta_text += f"  ·  {time_str[:8]}"

            meta_data = [[meta_text]]
            meta_table = Table(meta_data, colWidths=[170*mm])
            meta_table.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,-1), cat_color),
                ("TEXTCOLOR",    (0,0), (-1,-1), C_WHITE),
                ("FONTNAME",     (0,0), (-1,-1), "Helvetica-Bold"),
                ("FONTSIZE",     (0,0), (-1,-1), 8),
                ("TOPPADDING",   (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0), (-1,-1), 5),
                ("LEFTPADDING",  (0,0), (-1,-1), 10),
                ("ROUNDEDCORNERS", [4]),
            ]))
            story.append(meta_table)

            # Question text
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(question, self._styles["question"]))

            # Answer text
            story.append(Spacer(1, 2*mm))
            # Clean up answer for PDF (remove special chars)
            clean_answer = answer.replace("•", "-").replace("→", "->")
            story.append(Paragraph(clean_answer, self._styles["answer"]))

            story.append(Spacer(1, 6*mm))
            story.append(HRFlowable(
                width="100%", thickness=0.3,
                color=C_BORDER, spaceAfter=4
            ))

        return story

    def _build_footer(self) -> list:
        story = []
        story.append(Spacer(1, 8*mm))
        footer_text = (
            f"Generated by AI Interview Assistant · "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')} · "
            "Fully local — no cloud services"
        )
        story.append(Paragraph(footer_text, self._styles["footer"]))
        return story

    # ------------------------------------------------------------------ #
    # Styles
    # ------------------------------------------------------------------ #

    def _build_styles(self) -> dict:
        base = getSampleStyleSheet()
        return {
            "section_title": ParagraphStyle(
                "section_title",
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=C_TEXT,
                spaceAfter=4,
            ),
            "question": ParagraphStyle(
                "question",
                fontName="Helvetica-Bold",
                fontSize=10,
                textColor=C_TEXT,
                leftIndent=8,
                spaceAfter=2,
            ),
            "answer": ParagraphStyle(
                "answer",
                fontName="Helvetica",
                fontSize=9,
                textColor=C_MUTED,
                leftIndent=8,
                leading=14,
                spaceAfter=2,
            ),
            "muted": ParagraphStyle(
                "muted",
                fontName="Helvetica",
                fontSize=9,
                textColor=C_MUTED,
            ),
            "footer": ParagraphStyle(
                "footer",
                fontName="Helvetica",
                fontSize=8,
                textColor=C_MUTED,
                alignment=TA_CENTER,
            ),
        }