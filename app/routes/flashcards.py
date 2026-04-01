from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.services.gemini_service import generate_study_materials

router = APIRouter()


class FlashcardRequest(BaseModel):
    text: str


@router.post("/flashcards")
async def generate_flashcards(payload: FlashcardRequest):
    text = (payload.text or "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        materials = await run_in_threadpool(generate_study_materials, text)
        flashcards = materials.get("flashcards", [])

        return {
            "success": True,
            "flashcards": flashcards,
        }

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate flashcards")