import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.gemini_service import generate_study_materials
from app.db.session_service import save_study_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF and generate study materials using Gemini."""
    filename = (file.filename or "").strip()
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    if content_type and content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF")
    
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Extract text from PDF
        try:
            text = await run_in_threadpool(extract_text_from_pdf, file_bytes)
        except Exception:
            logger.exception("PDF extraction failed")
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        if not text:
            raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
        
        # Generate study materials (summary, quiz, flashcards)
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

        # Save to database (best effort). If save fails, still return generated materials.
        session_id = None
        try:
            session = await run_in_threadpool(
                save_study_session,
                text,
                summary=summary,
                quiz=quiz,
                flashcards=flashcards,
                filename=filename
            )
            if session and isinstance(session, list) and len(session) > 0 and isinstance(session[0], dict):
                session_id = session[0].get("id")
        except Exception:
            logger.exception("Database save failed; returning generated materials without persistence")

        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "summary": summary,
            "quiz": quiz,
            "flashcards": flashcards,
        }
    
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected upload error")
        raise HTTPException(status_code=500, detail="Upload failed")
