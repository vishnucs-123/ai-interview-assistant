"""
Test Phase 9: Analytics Dashboard.
Run: python -m tests.test_dashboard
Opens the dashboard with sample data.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from frontend.dashboard.dashboard_window import DashboardWindow


def test_dashboard():
    app = QApplication(sys.argv)

    window = DashboardWindow()
    window.show()

    # Sample data to populate the dashboard
    sample_history = [
        {"question": "Explain polymorphism in Java.",
         "answer": "Polymorphism allows objects to take multiple forms...",
         "category": "Technical", "topic": "Java"},
        {"question": "Tell me about yourself.",
         "answer": "I am a Java Full Stack developer...",
         "category": "Behavioral", "topic": "General"},
        {"question": "What is the difference between ArrayList and LinkedList?",
         "answer": "ArrayList uses dynamic array...",
         "category": "Technical", "topic": "Java"},
        {"question": "Write a function to reverse a linked list.",
         "answer": "Use two pointers prev and curr...",
         "category": "Coding", "topic": "DSA"},
        {"question": "How would you design a URL shortener?",
         "answer": "Use a hash function to map URLs...",
         "category": "System Design", "topic": "System Design"},
        {"question": "What are SOLID principles?",
         "answer": "SOLID stands for Single Responsibility...",
         "category": "Technical", "topic": "OOP"},
        {"question": "What is your expected salary?",
         "answer": "I am open to discussion based on...",
         "category": "HR", "topic": "General"},
        {"question": "Describe a challenge you faced in your project.",
         "answer": "During my internship at Pentagon Space...",
         "category": "Behavioral", "topic": "General"},
    ]

    sample_summary = {
        "total_questions": len(sample_history),
        "categories": {
            "Technical": 3,
            "Behavioral": 2,
            "Coding": 1,
            "System Design": 1,
            "HR": 1,
        },
        "topics_covered": ["Java", "DSA", "OOP", "System Design"],
    }

    def load_data():
        window.update_data(sample_summary, sample_history)
        print("Dashboard loaded with sample data.")

    QTimer.singleShot(500, load_data)

    print("Dashboard open. Close the window to exit.")
    sys.exit(app.exec())


if __name__ == "__main__":
    test_dashboard()