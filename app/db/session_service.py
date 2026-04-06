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

    if not normalized.get("filename"):
        text = normalized.get("input_text") or ""
        normalized["filename"] = text[:50] + "..." if len(text) > 50 else (text or f"Session #{normalized.get('id', '?')}")
    return normalized


def _apply_client_scope(query, client_key=None):
    if client_key:
        return query.eq("client_key", client_key)
    return query


def save_study_session(input_text, summary, quiz, flashcards, filename=None, client_key=None):
    data = {
        "input_text": input_text,
        "summary": summary,
        "quiz_json": quiz,
        "flashcards_json": flashcards,
        "filename": filename,
    }
    if client_key:
        data["client_key"] = client_key

    response = supabase.table("study_sessions").insert(data).execute()
    data = _require_success(response, "Save study session")
    return data or []


def get_all_study_sessions(client_key=None):
    query = supabase.table("study_sessions").select("id, input_text, filename, created_at")
    query = _apply_client_scope(query, client_key)
    response = query.order("created_at", desc=True).execute()
    data = _require_success(response, "Fetch history")

    # Extract filename from input_text (use first 50 chars as label)
    if data:
        for session in data:
            if session.get("filename"):
                continue
            if session.get("input_text"):
                # Use first 50 chars of text as filename
                text = session["input_text"]
                session["filename"] = text[:50] + "..." if len(text) > 50 else text
            else:
                session["filename"] = f"Session #{session.get('id', '?')}"

    # Deduplicate repeated rows that represent the same uploaded content.
    deduped = []
    seen = set()
    for session in data or []:
        filename = str(session.get("filename") or "").strip().lower()
        input_text = str(session.get("input_text") or "").strip().lower()
        signature = f"{filename}|{input_text}"
        key = signature if signature != "|" else str(session.get("id") or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(session)

    return deduped


def get_study_session_by_id(session_id, client_key=None):
    query = supabase.table("study_sessions").select("*").eq("id", session_id)
    query = _apply_client_scope(query, client_key)
    response = query.execute()
    data = _require_success(response, "Fetch history item")
    if data and len(data) > 0:
        return _normalize_session_payload(data[0])
    return None


def update_study_session_materials(session_id, summary=None, quiz=None, flashcards=None, client_key=None):
    update_payload = {}
    if summary is not None:
        update_payload["summary"] = summary
    if quiz is not None:
        update_payload["quiz_json"] = quiz
    if flashcards is not None:
        update_payload["flashcards_json"] = flashcards

    if not update_payload:
        return None

    query = supabase.table("study_sessions").update(update_payload).eq("id", session_id)
    query = _apply_client_scope(query, client_key)
    response = query.execute()
    data = _require_success(response, "Update study session")
    if data and len(data) > 0:
        return _normalize_session_payload(data[0])
    return None