"""
Persistent memory using SQLite.
Saves conversation history to disk so you can
review past interview sessions.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from backend.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "interviews.db"


class MemoryStore:
    """
    Persists interview sessions to SQLite database.

    Usage:
        store = MemoryStore()
        session_id = store.new_session()
        store.save_exchange(session_id, question, answer, category)
        history = store.get_session(session_id)
    """

    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._create_tables()
        logger.info(f"MemoryStore connected | db={DB_PATH}")

    def _create_tables(self) -> None:
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at  TEXT NOT NULL,
                ended_at    TEXT,
                summary     TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchanges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL,
                question    TEXT NOT NULL,
                answer      TEXT NOT NULL,
                category    TEXT,
                topic       TEXT,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        self._conn.commit()
        logger.info("Database tables ready")

    def new_session(self) -> int:
        """Start a new interview session. Returns session ID."""
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (started_at) VALUES (?)",
            (datetime.now().isoformat(),)
        )
        self._conn.commit()
        session_id = cursor.lastrowid
        logger.info(f"New session started | id={session_id}")
        return session_id

    def save_exchange(
        self,
        session_id: int,
        question: str,
        answer: str,
        category: str = "General",
        topic: str = "General"
    ) -> None:
        """Save a question-answer pair to the database."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO exchanges
                (session_id, question, answer, category, topic, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id, question, answer,
            category, topic,
            datetime.now().isoformat()
        ))
        self._conn.commit()
        logger.debug(f"Exchange saved | session={session_id}")

    def end_session(self, session_id: int, summary: str = "") -> None:
        """Mark session as ended."""
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET ended_at = ?, summary = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), summary, session_id))
        self._conn.commit()
        logger.info(f"Session ended | id={session_id}")

    def get_session(self, session_id: int) -> list[dict]:
        """Get all exchanges for a session."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT question, answer, category, topic, created_at
            FROM exchanges
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,))

        rows = cursor.fetchall()
        return [
            {
                "question": r[0],
                "answer": r[1],
                "category": r[2],
                "topic": r[3],
                "time": r[4]
            }
            for r in rows
        ]

    def get_all_sessions(self) -> list[dict]:
        """Get list of all past sessions."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, started_at, ended_at, summary
            FROM sessions
            ORDER BY started_at DESC
        """)
        rows = cursor.fetchall()
        return [
            {"id": r[0], "started": r[1], "ended": r[2], "summary": r[3]}
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()