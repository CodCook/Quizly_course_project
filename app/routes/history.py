from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import re
from app.db.session_service import (
    get_all_study_sessions,
    get_study_session_by_id,
)
from app.services.gemini_service import generate_study_materials, generate_summary

router = APIRouter()

_UUID_PATTERN = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


class HistoryGenerateRequest(BaseModel):
    action: str


def _ensure_even_flashcards(flashcards: list[dict]) -> list[dict]:
    if len(flashcards) % 2 == 1:
        return flashcards[:-1]
    return flashcards


@router.get("/history")
def fetch_all_history():
    return {"sessions": get_all_study_sessions()}


@router.get("/history/{session_id}")
def fetch_history_item(session_id: str):
    try:
        session = get_study_session_by_id(session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    return session


@router.post("/history/{session_id}/generate")
async def generate_from_history_item(session_id: str, payload: HistoryGenerateRequest):
    if not _UUID_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid study session id")

    action = (payload.action or "").strip().lower()
    if action not in {"summary", "quiz", "flashcards"}:
        raise HTTPException(status_code=400, detail="action must be one of: summary, quiz, flashcards")

    try:
        session = get_study_session_by_id(session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    text = (session.get("input_text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No source text found for this session")

    try:
        materials = await run_in_threadpool(generate_study_materials, text)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate study materials")

    if not isinstance(materials, dict):
        materials = {}

    summary = materials.get("summary", "") if isinstance(materials.get("summary", ""), str) else str(materials.get("summary", ""))
    quiz = materials.get("quiz", []) if isinstance(materials.get("quiz", []), list) else []
    flashcards = materials.get("flashcards", []) if isinstance(materials.get("flashcards", []), list) else []
    flashcards = _ensure_even_flashcards(flashcards)

    if action == "summary" and not summary.strip():
        try:
            summary = await run_in_threadpool(generate_summary, text)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to generate summary")

    return {
        "id": session.get("id"),
        "filename": session.get("filename"),
        "action": action,
        "summary": summary if action == "summary" else "",
        "quiz": quiz if action == "quiz" else [],
        "flashcards": flashcards if action == "flashcards" else [],
    }