from fastapi import APIRouter, HTTPException
from app.db.session_service import (
    get_all_study_sessions,
    get_study_session_by_id,
)

router = APIRouter()


@router.get("/history")
def fetch_all_history():
    return {"sessions": get_all_study_sessions()}


@router.get("/history/{session_id}")
def fetch_history_item(session_id: str):
    session = get_study_session_by_id(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Study session not found")

    return session