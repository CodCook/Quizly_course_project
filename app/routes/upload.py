import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.gemini_service import generate_summary
from app.db.session_service import save_study_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF and generate a summary using Gemini."""
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
        except Exception as e:
            logger.exception("PDF extraction failed")
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        if not text:
            raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
        
        # Generate summary
        try:
            summary = await run_in_threadpool(generate_summary, text)
        except Exception as e:
            logger.exception("Gemini summary generation failed")
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Save to database (best effort). If save fails, still return summary.
        session_id = None
        try:
            session = await run_in_threadpool(
                save_study_session,
                filename,
                summary=summary,
                quiz=[],
                flashcards=[]
            )
            if session and isinstance(session, list) and len(session) > 0 and isinstance(session[0], dict):
                session_id = session[0].get("id")
        except Exception:
            logger.warning("Database save failed; returning summary without persistence")
        
        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "summary": summary
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected upload error")
        raise HTTPException(status_code=500, detail="Upload failed")
