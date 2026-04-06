import logging
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.services.document_extractor import extract_text_from_upload, is_supported_upload
from app.services.gemini_service import generate_study_materials, generate_summary
from app.db.session_service import save_study_session, update_study_session_materials

router = APIRouter()
logger = logging.getLogger(__name__)

_UPLOAD_CACHE: dict[str, dict[str, str]] = {}
_VALID_ACTIONS = {"summary", "quiz", "flashcards"}


def _ensure_even_flashcards(flashcards: list[dict]) -> list[dict]:
    if len(flashcards) % 2 == 1:
        return flashcards[:-1]
    return flashcards


class GenerateUploadRequest(BaseModel):
    upload_id: str
    action: str


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a supported study file and extract text."""
    filename = (file.filename or "").strip()
    if not is_supported_upload(filename):
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and PPTX files are supported")
    
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Extract text from uploaded document
        try:
            text = await run_in_threadpool(extract_text_from_upload, file_bytes, filename)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            logger.exception("Document extraction failed")
            raise HTTPException(status_code=400, detail="Failed to extract text from file")
        
        if not text:
            raise HTTPException(status_code=400, detail="No text could be extracted from file")

        upload_id = str(uuid4())
        _UPLOAD_CACHE[upload_id] = {"text": text, "filename": filename, "session_id": ""}

        return {
            "success": True,
            "upload_id": upload_id,
            "filename": filename,
            "actions": sorted(_VALID_ACTIONS),
        }
    
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected upload error")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/upload/generate")
async def generate_from_uploaded_file(
    payload: GenerateUploadRequest,
    x_client_key: str | None = Header(default=None),
):
    upload_id = (payload.upload_id or "").strip()
    action = (payload.action or "").strip().lower()

    if not upload_id:
        raise HTTPException(status_code=400, detail="upload_id is required")
    if action not in _VALID_ACTIONS:
        raise HTTPException(status_code=400, detail="action must be one of: summary, quiz, flashcards")

    cached = _UPLOAD_CACHE.get(upload_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Upload not found or expired")

    text = cached["text"]
    filename = cached["filename"]
    existing_session_id = (cached.get("session_id") or "").strip()

    try:
        materials = await run_in_threadpool(generate_study_materials, text)
    except Exception:
        logger.exception("Gemini study material generation failed")
        raise HTTPException(status_code=500, detail="Failed to generate study materials")

    if not isinstance(materials, dict):
        materials = {}

    summary = materials.get("summary", "") if isinstance(materials.get("summary", ""), str) else str(materials.get("summary", ""))
    quiz = materials.get("quiz", []) if isinstance(materials.get("quiz", []), list) else []
    flashcards = materials.get("flashcards", []) if isinstance(materials.get("flashcards", []), list) else []

    # Fallback for summary action when JSON parse returns empty summary.
    if action == "summary" and not summary.strip():
        try:
            summary = await run_in_threadpool(generate_summary, text)
        except Exception:
            logger.exception("Gemini summary fallback failed")
            raise HTTPException(status_code=500, detail="Failed to generate summary")

    filtered_summary = summary if action == "summary" else ""
    filtered_quiz = quiz if action == "quiz" else []
    filtered_flashcards = flashcards if action == "flashcards" else []
    filtered_flashcards = _ensure_even_flashcards(filtered_flashcards)

    session_id = existing_session_id or None
    try:
        if existing_session_id:
            await run_in_threadpool(
                update_study_session_materials,
                existing_session_id,
                summary=filtered_summary if action == "summary" else None,
                quiz=filtered_quiz if action == "quiz" else None,
                flashcards=filtered_flashcards if action == "flashcards" else None,
                client_key=x_client_key,
            )
            session_id = existing_session_id
        else:
            session = await run_in_threadpool(
                save_study_session,
                text,
                summary=filtered_summary,
                quiz=filtered_quiz,
                flashcards=filtered_flashcards,
                filename=filename,
                client_key=x_client_key,
            )
            if session and isinstance(session, list) and len(session) > 0 and isinstance(session[0], dict):
                session_id = session[0].get("id")
                if session_id:
                    cached["session_id"] = str(session_id)
    except Exception:
        logger.exception("Database save failed; returning generated materials without persistence")

    return {
        "success": True,
        "session_id": session_id,
        "filename": filename,
        "action": action,
        "summary": filtered_summary,
        "quiz": filtered_quiz,
        "flashcards": filtered_flashcards,
    }
