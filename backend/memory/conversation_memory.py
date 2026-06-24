"""
Conversation Memory.
Stores the last N question-answer pairs and provides
context to the LLM for follow-up questions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryEntry:
    question: str
    answer: str
    category: str
    topic: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S")
    )


class ConversationMemory:
    """
    Maintains a rolling window of the last N interview exchanges.

    Usage:
        memory = ConversationMemory(max_entries=20)
        memory.add("Explain OOP", "OOP is...", "Technical", "Java")
        context = memory.get_context()   # pass to LLM prompt
    """

    def __init__(self, max_entries: int = 20):
        self._entries: deque[MemoryEntry] = deque(maxlen=max_entries)
        self.max_entries = max_entries
        logger.info(f"ConversationMemory initialized | max={max_entries}")

    def add(
        self,
        question: str,
        answer: str,
        category: str = "General",
        topic: str = "General"
    ) -> None:
        """Store a new question-answer pair."""
        entry = MemoryEntry(
            question=question,
            answer=answer,
            category=category,
            topic=topic
        )
        self._entries.append(entry)
        logger.debug(f"Memory stored [{len(self._entries)}/{self.max_entries}]: {question[:50]}")

    def get_context(self, last_n: int = 5) -> str:
        """
        Return the last N exchanges formatted as LLM context string.
        Passed into prompts so the LLM knows what was already discussed.
        """
        if not self._entries:
            return ""

        recent = list(self._entries)[-last_n:]
        lines = ["Previous interview context:"]

        for i, entry in enumerate(recent, 1):
            lines.append(f"\n[{i}] Q ({entry.category}): {entry.question}")
            # Truncate long answers to save tokens
            short_answer = entry.answer[:200] + "..." if len(entry.answer) > 200 else entry.answer
            lines.append(f"    A: {short_answer}")

        return "\n".join(lines)

    def get_topics_covered(self) -> list[str]:
        """Return list of unique topics discussed so far."""
        return list({e.topic for e in self._entries if e.topic != "General"})

    def get_summary(self) -> dict:
        """Return analytics summary of the conversation."""
        if not self._entries:
            return {}

        categories = {}
        for e in self._entries:
            categories[e.category] = categories.get(e.category, 0) + 1

        return {
            "total_questions": len(self._entries),
            "categories": categories,
            "topics_covered": self.get_topics_covered(),
            "start_time": self._entries[0].timestamp if self._entries else None,
            "last_time": self._entries[-1].timestamp if self._entries else None,
        }

    def clear(self) -> None:
        self._entries.clear()
        logger.info("Conversation memory cleared")

    def __len__(self) -> int:
        return len(self._entries)

    def all_entries(self) -> list[MemoryEntry]:
        return list(self._entries)