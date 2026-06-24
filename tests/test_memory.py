"""
Test Phase 7: Conversation Memory.
Run: python -m tests.test_memory
"""

from backend.memory.conversation_memory import ConversationMemory
from backend.memory.memory_store import MemoryStore


def test_memory():
    print("=== Phase 7: Memory Test ===\n")

    # In-memory context
    memory = ConversationMemory(max_entries=5)

    memory.add("Explain OOP", "OOP stands for...", "Technical", "Java")
    memory.add("Tell me about yourself", "I am a...", "Behavioral", "General")
    memory.add("What is polymorphism?", "Polymorphism is...", "Technical", "Java")

    print("Context passed to LLM:")
    print(memory.get_context())
    print()
    print("Topics covered:", memory.get_topics_covered())
    print("Summary:", memory.get_summary())

    # Persistent storage
    print("\n--- SQLite persistence test ---")
    store = MemoryStore()
    session_id = store.new_session()
    store.save_exchange(session_id, "Explain OOP", "OOP is...", "Technical", "Java")
    store.save_exchange(session_id, "Tell me about yourself", "I am...", "Behavioral", "General")
    store.end_session(session_id, summary="2 questions answered")

    history = store.get_session(session_id)
    print(f"Saved {len(history)} exchanges for session {session_id}")
    for h in history:
        print(f"  [{h['category']}] {h['question'][:50]}")

    all_sessions = store.get_all_sessions()
    print(f"\nTotal sessions in DB: {len(all_sessions)}")
    store.close()

    print("\n=== Memory test complete ===")


if __name__ == "__main__":
    test_memory()