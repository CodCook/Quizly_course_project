from app.db.supabase_client import supabase


def _require_success(response, operation_name: str):
    if response.error:
        raise RuntimeError(f"{operation_name} failed: {response.error}")
    return response.data


def save_study_session(input_text, summary, quiz, flashcards):
    data = {
        "input_text": input_text,
        "summary": summary,
        "quiz_json": quiz,
        "flashcards_json": flashcards,
    }

    response = supabase.table("study_sessions").insert(data).execute()
    data = _require_success(response, "Save study session")
    return data or []


def get_all_study_sessions():
    response = (
        supabase.table("study_sessions")
        .select("id, input_text, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    data = _require_success(response, "Fetch history")
    return data or []


def get_study_session_by_id(session_id):
    response = (
        supabase.table("study_sessions")
        .select("*")
        .eq("id", session_id)
        .execute()
    )
    data = _require_success(response, "Fetch history item")
    if data and len(data) > 0:
        return data[0]
    return None