from app.routes.history import router as history_router

app.include_router(history_router, prefix="/api", tags=["History"])