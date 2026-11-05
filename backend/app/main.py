"""Personal Learning Tracker — backend.
Run: uvicorn app.main:app --reload  (from backend/)
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers import checklist, days, journal, progress, tracks
from .seed import seed


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Personal Learning Tracker", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(tracks.router, prefix="/api")
app.include_router(days.router, prefix="/api")
app.include_router(checklist.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(progress.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True}
