"""
Test Phase 3: Question Detection.
Run: python -m tests.test_question_detector
No mic needed — uses hardcoded sample questions.
"""

from backend.transcriber.question_detector import QuestionDetector


def test_detector():
    print("=== Phase 3: Question Detection Test ===\n")

    detector = QuestionDetector()

    samples = [
        "Explain polymorphism in Java.",
        "Tell me about yourself.",
        "What is your expected salary?",
        "Write a program to reverse a linked list.",
        "How would you design a URL shortener?",
        "What are the SOLID principles?",
        "Describe a time you handled a conflict in your team.",
        "What is the difference between ArrayList and LinkedList?",
        "Can you join immediately?",
        "The weather is nice today.",          # Not a question
    ]

    for text in samples:
        result = detector.detect(text)
        print(f"Input    : {text}")
        print(f"Result   : {result}")
        print(f"Confidence: {result.confidence}")
        print("-" * 60)


if __name__ == "__main__":
    test_detector()