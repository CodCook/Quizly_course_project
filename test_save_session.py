from app.db.session_service import save_study_session, get_all_study_sessions

sample_quiz = [
    {
        "question": "What is Python?",
        "options": ["A snake", "A programming language", "A database", "A browser"],
        "answer": "A programming language",
    }
]

sample_flashcards = [
    {
        "term": "Python",
        "definition": "A high-level programming language."
    }
]

print("Testing save_study_session...")
try:
    saved = save_study_session(
        input_text="Python basics",
        summary="Python is a popular programming language used for many purposes.",
        quiz=sample_quiz,
        flashcards=sample_flashcards,
    )
    print("✅ Save operation completed")
    print("Saved session:")
    print(saved)
except Exception as e:
    print(f"❌ Error saving session: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting get_all_study_sessions...")
try:
    all_sessions = get_all_study_sessions()
    print("✅ Get all sessions completed")
    print("All sessions:")
    print(all_sessions)
except Exception as e:
    print(f"❌ Error getting sessions: {e}")
    import traceback
    traceback.print_exc()