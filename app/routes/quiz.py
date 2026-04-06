from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gemini_service import generate_quiz_from_topic

router = APIRouter()

class TopicRequest(BaseModel):
    topic: str

@router.post("/generate")
def generate_quiz(request: TopicRequest):
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    
    quiz = generate_quiz_from_topic(request.topic.strip())
    
    if not quiz:
        raise HTTPException(status_code=500, detail="Failed to generate quiz for the given topic.")
        
    return {"quiz": quiz}
