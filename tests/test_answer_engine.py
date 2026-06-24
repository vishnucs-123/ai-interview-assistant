"""
Test Phase 4: Answer Generation.
Run: python -m tests.test_answer_engine
Requires Ollama running with llama3.2 pulled.
"""

from backend.llm.answer_engine import AnswerEngine
from backend.transcriber.question_detector import QuestionDetector


def test_answer_engine():
    print("=== Phase 4: Answer Generation Test ===\n")

    engine = AnswerEngine(model="llama3.2")

    print("Checking Ollama connection...")
    if not engine.check_ollama_running():
        print("\nOllama not running or model not found.")
        print("Fix: Make sure Ollama is installed and run: ollama pull llama3.2")
        return

    print("Ollama ready!\n")

    detector = QuestionDetector()

    test_questions = [
        "Explain polymorphism in Java.",
        "Tell me about yourself.",
        "What is your expected salary?",
        "Write a function to check if a string is a palindrome.",
    ]

    for question_text in test_questions:
        print(f"Processing: {question_text}")
        detected = detector.detect(question_text)
        answer = engine.generate(detected)
        print(answer)
        print()


if __name__ == "__main__":
    test_answer_engine()