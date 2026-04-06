from app.db.supabase_client import supabase


def _require_success(response, operation_name: str):
    if response.error:
        raise RuntimeError(f"{operation_name} failed: {response.error}")
    return response.data


def _normalize_session_payload(session: dict) -> dict:
    normalized = dict(session)
    if "quiz" not in normalized:
        normalized["quiz"] = normalized.get("quiz_json", []) or []
    if "flashcards" not in normalized:
        normalized["flashcards"] = normalized.get("flashcards_json", []) or []
    return normalized


def save_study_session(input_text, summary, quiz, flashcards, filename=None):
    data = {
        "input_text": input_text,
        "summary": summary,
        "quiz_json": quiz,
        "flashcards_json": flashcards,
        "filename": filename,
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
    
    # Extract filename from input_text (use first 50 chars as label)
    if data:
        for session in data:
            if session.get("input_text"):
                # Use first 50 chars of text as filename
                text = session["input_text"]
                session["filename"] = text[:50] + "..." if len(text) > 50 else text
            else:
                session["filename"] = f"Session #{session.get('id', '?')}"
    
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
        return _normalize_session_payload(data[0])
    return None


def update_study_session_materials(session_id, summary=None, quiz=None, flashcards=None):
    update_payload = {}
    if summary is not None:
        update_payload["summary"] = summary
    if quiz is not None:
        update_payload["quiz_json"] = quiz
    if flashcards is not None:
        update_payload["flashcards_json"] = flashcards

    if not update_payload:
        return None

    response = (
        supabase.table("study_sessions")
        .update(update_payload)
        .eq("id", session_id)
        .execute()
    )
    data = _require_success(response, "Update study session")
    if data and len(data) > 0:
        return _normalize_session_payload(data[0])
    return None