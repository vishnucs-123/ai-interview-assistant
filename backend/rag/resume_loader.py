"""
Resume PDF Loader.
Extracts text from a resume PDF and chunks it
into sections for embedding.
"""

import re
from pathlib import Path
from PyPDF2 import PdfReader
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ResumeLoader:
    """
    Loads and parses a resume PDF into text chunks.

    Usage:
        loader = ResumeLoader()
        chunks = loader.load("resume.pdf")
    """

    def __init__(self):
        logger.info("ResumeLoader initialized")

    def load(self, pdf_path: str) -> list[str]:
        """
        Extract text from PDF and split into chunks.
        Returns list of text chunks ready for embedding.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume not found: {pdf_path}")

        logger.info(f"Loading resume: {path.name}")

        # Extract raw text from all pages
        raw_text = self._extract_text(path)

        if not raw_text.strip():
            raise ValueError("Could not extract text from PDF. Is it a scanned image?")

        # Split into meaningful chunks
        chunks = self._chunk_text(raw_text)

        logger.info(f"Resume loaded | {len(chunks)} chunks extracted")
        return chunks

    def _extract_text(self, path: Path) -> str:
        """Extract all text from PDF pages."""
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split resume text into chunks by section.
        Falls back to paragraph splitting if no sections detected.
        """
        # Common resume section headers
        section_pattern = re.compile(
            r'\n(?=(?:EXPERIENCE|EDUCATION|SKILLS|PROJECTS|'
            r'ACHIEVEMENTS|CERTIFICATIONS|SUMMARY|OBJECTIVE|'
            r'INTERNSHIP|WORK HISTORY|TECHNICAL SKILLS)'
            r')',
            re.IGNORECASE
        )

        sections = section_pattern.split(text)

        # If no sections found, split by paragraph
        if len(sections) <= 1:
            sections = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Filter out very short chunks (< 30 chars)
        chunks = [s.strip() for s in sections if len(s.strip()) > 30]

        return chunks