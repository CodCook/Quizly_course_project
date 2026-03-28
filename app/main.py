from fastapi import FastAPI
from app.routes.history import router as history_router

app = FastAPI(title="Quizly")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(history_router, prefix="/api", tags=["History"])