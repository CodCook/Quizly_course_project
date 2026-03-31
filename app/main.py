from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.history import router as history_router
from app.routes.upload import router as upload_router
from app.routes.flashcards import router as flashcards_router


app = FastAPI(title="Quizly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(INDEX_FILE)


@app.get("/health")
def health():
    return {"status": "ok", "app": "Quizly"}


app.include_router(history_router, prefix="/api", tags=["History"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(flashcards_router, prefix="/api", tags=["Flashcards"])
