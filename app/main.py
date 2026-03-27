from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.history import router as history_router


app = FastAPI(title="Quizly API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health():
	return {"status": "ok", "app": "Quizly"}


app.include_router(history_router, prefix="/api", tags=["History"])