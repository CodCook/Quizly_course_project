from fastapi import APIRouter, HTTPException, Header
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import re
from app.db.session_service import (
    get_all_study_sessions,
    get_study_session_by_id,
    update_study_session_materials,
)
from app.services.gemini_service import (
    generate_study_materials,
    generate_summary,
    generate_quiz_from_text,
    generate_flashcards_from_text,
)

router = APIRouter()

_UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


class HistoryGenerateRequest(BaseModel):
    action: str


def _ensure_even_flashcards(flashcards: list[dict]) -> list[dict]:
    if len(flashcards) % 2 == 1:
        return flashcards[:-1]
    return flashcards


@router.get("/history")
def fetch_all_history(x_client_key: str | None = Header(default=None)):
    return {"sessions": get_all_study_sessions(client_key=x_client_key)}


@router.get("/history/{session_id}")
def fetch_history_item(session_id: str, x_client_key: str | None = Header(default=None)):
    try:
        session = get_study_session_by_id(session_id, client_key=x_client_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    return session


@router.post("/history/{session_id}/generate")
async def generate_from_history_item(
    session_id: str,
    payload: HistoryGenerateRequest,
    x_client_key: str | None = Header(default=None),
):
    if not _UUID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid study session id")

    action = (payload.action or "").strip().lower()
    if action not in {"summary", "quiz", "flashcards"}:
        raise HTTPException(status_code=400, detail="action must be one of: summary, quiz, flashcards")

    try:
        session = get_study_session_by_id(session_id, client_key=x_client_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    text = (session.get("input_text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No source text found for this session")

    summary = (session.get("summary") or "").strip()
    quiz = session.get("quiz", []) if isinstance(session.get("quiz", []), list) else []
    flashcards = session.get("flashcards", []) if isinstance(session.get("flashcards", []), list) else []
    flashcards = _ensure_even_flashcards(flashcards)

    # If requested material already exists, return it immediately.
    if action == "summary" and summary:
        return {
            "id": session.get("id"),
            "session_id": session.get("id"),
            "filename": session.get("filename"),
            "action": action,
            "summary": summary,
            "quiz": [],
            "flashcards": [],
        }
    if action == "flashcards" and flashcards:
        return {
            "id": session.get("id"),
            "session_id": session.get("id"),
            "filename": session.get("filename"),
            "action": action,
            "summary": "",
            "quiz": [],
            "flashcards": flashcards,
        }

    if action == "summary":
        try:
            materials = await run_in_threadpool(generate_study_materials, text)
        except Exception:
            materials = {}

        if not isinstance(materials, dict):
            materials = {}

        generated_summary = materials.get("summary", "") if isinstance(materials.get("summary", ""), str) else str(materials.get("summary", ""))
        if generated_summary.strip():
            summary = generated_summary.strip()
        else:
            try:
                summary = await run_in_threadpool(generate_summary, text)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to generate summary: {exc}")
    elif action == "quiz":
        try:
            quiz = await run_in_threadpool(generate_quiz_from_text, text)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {exc}")

        if not quiz:
            raise HTTPException(status_code=500, detail="Failed to generate quiz")
    else:
        try:
            materials = await run_in_threadpool(generate_study_materials, text)
        except Exception:
            materials = {}

        if not isinstance(materials, dict):
            materials = {}

        generated_flashcards = materials.get("flashcards", []) if isinstance(materials.get("flashcards", []), list) else []
        generated_flashcards = _ensure_even_flashcards(generated_flashcards)

        if generated_flashcards:
            flashcards = generated_flashcards
        else:
            try:
                flashcards = await run_in_threadpool(generate_flashcards_from_text, text)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {exc}")

        flashcards = _ensure_even_flashcards(flashcards)
        if not flashcards:
            raise HTTPException(status_code=500, detail="Failed to generate flashcards")

    # Persist newly generated material so future clicks don't regenerate.
    try:
        update_study_session_materials(
            session_id,
            summary=summary if action == "summary" else None,
            quiz=quiz if action == "quiz" else None,
            flashcards=flashcards if action == "flashcards" else None,
            client_key=x_client_key,
        )
    except Exception:
        # Keep response successful even if persistence fails.
        pass

    return {
        "id": session.get("id"),
        "session_id": session.get("id"),
        "filename": session.get("filename"),
        "action": action,
        "summary": summary if action == "summary" else "",
        "quiz": quiz if action == "quiz" else [],
        "flashcards": flashcards if action == "flashcards" else [],
    }