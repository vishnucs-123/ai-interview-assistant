"""
Test Phase 8: Resume RAG.
Run: python -m tests.test_rag
Put your resume PDF at: models/resume.pdf
"""

from pathlib import Path
from backend.rag.resume_rag import ResumeRAG
from backend.transcriber.question_detector import QuestionDetector
from backend.llm.answer_engine import AnswerEngine


def test_rag():
    print("=== Phase 8: Resume RAG Test ===\n")

    resume_path = Path("models/resume.pdf")

    if not resume_path.exists():
        print("No resume found at models/resume.pdf")
        print("Creating a demo test with dummy text instead...\n")
        _test_without_resume()
        return

    rag = ResumeRAG()
    print(f"Loading resume: {resume_path}")
    chunks = rag.load_resume(str(resume_path))
    print(f"Indexed {chunks} chunks from your resume\n")

    test_questions = [
        "Tell me about your projects.",
        "What is your technical experience?",
        "Tell me about yourself.",
    ]

    detector = QuestionDetector()
    engine = AnswerEngine()

    for q in test_questions:
        print(f"Q: {q}")
        context = rag.get_context(q)
        detected = detector.detect(q)
        answer = engine.generate_with_resume(detected, resume_context=context)
        print(f"A: {answer.answer[:300]}...")
        print("-" * 60)


def _test_without_resume():
    """Test RAG pipeline without a real resume."""
    rag = ResumeRAG()

    # Manually add some chunks to simulate a resume
    rag._collection.add(
        documents=[
            "Java Full Stack Developer with 6 months internship at Pentagon Space Pvt Ltd Bengaluru",
            "Projects: Resume Copilot (Next.js, Prisma, PostgreSQL), Criminal Face ID System (Python, OpenCV)",
            "Skills: Java, Spring Boot, React, SQL, Python, REST APIs",
            "Education: B.E Computer Science, GNDEC Bidar, VTU, 2026",
        ],
        ids=["c0", "c1", "c2", "c3"]
    )
    rag._resume_loaded = True

    question = "Tell me about your projects."
    context = rag.get_context(question)
    print("Resume context retrieved:")
    print(context)
    print("\n=== RAG test complete ===")


if __name__ == "__main__":
    test_rag()