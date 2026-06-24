"""
Question Detection Engine.
Analyzes transcribed text to determine:
- Is it a question?
- What category? (Technical, Behavioral, HR, Coding, System Design)
- What topic? (Java, Python, OOP, etc.)
- What keywords?
"""

import re
from dataclasses import dataclass, field
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data model for a detected question
# ---------------------------------------------------------------------------

@dataclass
class DetectedQuestion:
    text: str
    is_question: bool
    category: str           # Technical | Behavioral | HR | Coding | System Design
    topic: str              # Java | Python | SQL | OOP | General | etc.
    keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0

    def __str__(self):
        return (
            f"Question: {self.is_question} | "
            f"Category: {self.category} | "
            f"Topic: {self.topic} | "
            f"Keywords: {self.keywords}"
        )


# ---------------------------------------------------------------------------
# Keyword maps — used to classify category and topic
# ---------------------------------------------------------------------------

TECHNICAL_KEYWORDS = {
    # Java
    "java": "Java", "jvm": "Java", "garbage collection": "Java",
    "polymorphism": "Java", "inheritance": "Java", "abstraction": "Java",
    "encapsulation": "Java", "interface": "Java", "abstract class": "Java",
    "spring": "Spring", "spring boot": "Spring", "hibernate": "Java",
    "collections": "Java", "arraylist": "Java", "hashmap": "Java",
    "multithreading": "Java", "thread": "Java", "synchronization": "Java",
    "exception": "Java", "try catch": "Java", "stream": "Java",
    "lambda": "Java", "generics": "Java", "serialization": "Java",

    # Python
    "python": "Python", "django": "Python", "flask": "Python",
    "decorator": "Python", "generator": "Python", "list comprehension": "Python",

    # DSA
    "array": "DSA", "linked list": "DSA", "tree": "DSA", "graph": "DSA",
    "binary search": "DSA", "sorting": "DSA", "recursion": "DSA",
    "dynamic programming": "DSA", "stack": "DSA", "queue": "DSA",
    "hash table": "DSA", "heap": "DSA", "trie": "DSA",

    # SQL / DB
    "sql": "SQL", "database": "SQL", "join": "SQL", "index": "SQL",
    "normalization": "SQL", "transaction": "SQL", "acid": "SQL",
    "primary key": "SQL", "foreign key": "SQL", "query": "SQL",

    # System Design
    "microservices": "System Design", "rest api": "System Design",
    "load balancer": "System Design", "cache": "System Design",
    "kafka": "System Design", "docker": "System Design",
    "kubernetes": "System Design", "scalability": "System Design",
    "architecture": "System Design",

    # General CS
    "oop": "OOP", "object oriented": "OOP", "design pattern": "OOP",
    "solid": "OOP", "singleton": "OOP", "factory": "OOP",
}

BEHAVIORAL_KEYWORDS = [
    "tell me about yourself", "introduce yourself",
    "strength", "weakness", "challenge", "conflict",
    "team", "leadership", "failure", "success",
    "proud", "difficult situation", "handle pressure",
    "why should we hire", "why do you want",
    "where do you see yourself", "5 years",
    "achievement", "mistake", "feedback", "criticism",
]

CODING_KEYWORDS = [
    "write a program", "write code", "implement",
    "code", "algorithm", "function", "two sum",
    "reverse", "palindrome", "fibonacci", "factorial",
    "find the", "print the", "return the", "lru cache",
    "binary tree", "linked list", "matrix",
]

HR_KEYWORDS = [
    "salary", "notice period", "relocate", "remote",
    "available", "join", "offer", "compensation",
    "work life balance", "culture", "why this company",
    "expectations", "visa", "contract",
]

SYSTEM_DESIGN_KEYWORDS = [
    "design a system", "design an", "how would you design",
    "architect", "how does", "explain the architecture",
    "how would you build", "scalable", "high availability",
]

# Question-indicating words and patterns
QUESTION_STARTERS = [
    "what", "why", "how", "when", "where", "who", "which",
    "explain", "describe", "tell me", "can you", "could you",
    "do you", "have you", "would you", "is there", "are there",
    "define", "differentiate", "compare", "implement", "write",
]


# ---------------------------------------------------------------------------
# Main detector class
# ---------------------------------------------------------------------------

class QuestionDetector:
    """
    Detects interview questions from transcribed text.

    Usage:
        detector = QuestionDetector()
        result = detector.detect("Explain polymorphism in Java.")
        print(result)
    """

    def __init__(self):
        logger.info("QuestionDetector initialized")

    def detect(self, text: str) -> DetectedQuestion:
        """
        Analyze text and return a DetectedQuestion.
        """
        text = text.strip()
        lower = text.lower()

        is_question = self._is_question(lower)
        category = self._detect_category(lower)
        topic = self._detect_topic(lower)
        keywords = self._extract_keywords(lower)
        confidence = self._calculate_confidence(is_question, category, keywords)

        result = DetectedQuestion(
            text=text,
            is_question=is_question,
            category=category,
            topic=topic,
            keywords=keywords,
            confidence=confidence
        )

        logger.debug(f"Detected: {result}")
        return result

    def _is_question(self, text: str) -> bool:
        """
        Returns True if the text looks like an interview question.
        Checks for:
        - Question mark
        - Question starter words
        - Command-style questions (Explain X, Implement Y)
        """
        # Direct question mark
        if "?" in text:
            return True

        # Starts with a question word
        for starter in QUESTION_STARTERS:
            if text.startswith(starter):
                return True

        # Mid-sentence question pattern
        question_pattern = r'\b(what|why|how|explain|describe|define|implement|write)\b'
        if re.search(question_pattern, text):
            return True

        return False

    def _detect_category(self, text: str) -> str:
        """
        Classify into: Technical | Behavioral | Coding | HR | System Design | General
        """
        # Check system design first (more specific)
        for kw in SYSTEM_DESIGN_KEYWORDS:
            if kw in text:
                return "System Design"

        # Check coding
        for kw in CODING_KEYWORDS:
            if kw in text:
                return "Coding"

        # Check technical
        for kw in TECHNICAL_KEYWORDS:
            if kw in text:
                return "Technical"

        # Check behavioral
        for kw in BEHAVIORAL_KEYWORDS:
            if kw in text:
                return "Behavioral"

        # Check HR
        for kw in HR_KEYWORDS:
            if kw in text:
                return "HR"

        return "General"

    def _detect_topic(self, text: str) -> str:
        """
        Extract the specific topic (Java, Python, SQL, etc.)
        """
        for keyword, topic in TECHNICAL_KEYWORDS.items():
            if keyword in text:
                return topic
        return "General"

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract all matching keywords found in the text.
        """
        found = []
        all_keywords = (
            list(TECHNICAL_KEYWORDS.keys()) +
            BEHAVIORAL_KEYWORDS +
            CODING_KEYWORDS +
            HR_KEYWORDS
        )
        for kw in all_keywords:
            if kw in text and kw not in found:
                found.append(kw)
        return found[:5]  # Return top 5 only

    def _calculate_confidence(
        self,
        is_question: bool,
        category: str,
        keywords: list[str]
    ) -> float:
        """
        Simple confidence score based on signals found.
        """
        score = 0.0
        if is_question:
            score += 0.5
        if category != "General":
            score += 0.3
        if keywords:
            score += min(len(keywords) * 0.05, 0.2)
        return round(min(score, 1.0), 2)