"""
Test Phase 10: PDF Export.
Run: python -m tests.test_pdf_export
Generates a sample PDF in the reports/ folder.
"""

from backend.utils.pdf_exporter import PDFExporter


def test_pdf_export():
    print("=== Phase 10: PDF Export Test ===\n")

    exporter = PDFExporter()

    session_data = {
        "started_at": "2026-06-08T10:00:00",
        "ended_at":   "2026-06-08T10:45:00",
        "summary": {
            "total_questions": 5,
            "categories": {
                "Technical": 3,
                "Behavioral": 1,
                "Coding": 1,
            },
            "topics_covered": ["Java", "DSA", "OOP"],
        },
        "history": [
            {
                "question": "Explain polymorphism in Java.",
                "answer": (
                    "Polymorphism allows objects to take multiple forms.\n"
                    "- Compile-time: Method overloading\n"
                    "- Runtime: Method overriding via inheritance\n"
                    "Example: Animal a = new Dog(); a.speak();"
                ),
                "category": "Technical",
                "topic": "Java",
                "time": "10:03:21",
            },
            {
                "question": "Tell me about yourself.",
                "answer": (
                    "I am a Java Full Stack developer with 6 months of "
                    "internship experience at Pentagon Space Pvt. Ltd. "
                    "I built REST APIs using Spring Boot and worked on "
                    "React frontends. I am passionate about clean code "
                    "and system design."
                ),
                "category": "Behavioral",
                "topic": "General",
                "time": "10:08:45",
            },
            {
                "question": "What are the SOLID principles?",
                "answer": (
                    "SOLID stands for:\n"
                    "- S: Single Responsibility\n"
                    "- O: Open/Closed\n"
                    "- L: Liskov Substitution\n"
                    "- I: Interface Segregation\n"
                    "- D: Dependency Inversion"
                ),
                "category": "Technical",
                "topic": "OOP",
                "time": "10:15:10",
            },
            {
                "question": "Write a function to reverse a linked list.",
                "answer": (
                    "Approach: Use two pointers prev and curr.\n"
                    "Time: O(n) | Space: O(1)\n\n"
                    "ListNode reverse(ListNode head) {\n"
                    "  ListNode prev = null, curr = head;\n"
                    "  while (curr != null) {\n"
                    "    ListNode next = curr.next;\n"
                    "    curr.next = prev;\n"
                    "    prev = curr; curr = next;\n"
                    "  }\n"
                    "  return prev;\n"
                    "}"
                ),
                "category": "Coding",
                "topic": "DSA",
                "time": "10:22:33",
            },
            {
                "question": "What is the difference between HashMap and TreeMap?",
                "answer": (
                    "HashMap: O(1) avg for get/put, unordered, allows null key.\n"
                    "TreeMap: O(log n) for get/put, sorted by key, no null key.\n"
                    "Use HashMap for fast lookups, TreeMap when sorted order needed."
                ),
                "category": "Technical",
                "topic": "Java",
                "time": "10:30:15",
            },
        ],
    }

    path = exporter.export(session_data)
    print(f"PDF generated at: {path}")
    print("\nOpen the reports/ folder to view it.")
    print("=== PDF Export test complete ===")


if __name__ == "__main__":
    test_pdf_export()