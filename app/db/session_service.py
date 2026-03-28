from app.db.supabase_client import supabase


def save_study_session(input_text, summary, quiz, flashcards):
    data = {
        "input_text": input_text,
        "summary": summary,
        "quiz_json": quiz,
        "flashcards_json": flashcards,
    }

    response = supabase.table("study_sessions").insert(data).execute()
    return response.data


def get_all_study_sessions():
    response = (
        supabase.table("study_sessions")
        .select("id, input_text, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


def get_study_session_by_id(session_id):
    response = (
        supabase.table("study_sessions")
        .select("*")
        .eq("id", session_id)
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None