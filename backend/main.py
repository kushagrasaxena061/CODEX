from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.database.connection import engine, Base, get_db
from backend.llm.ollama_client import check_ollama_health
from backend.api.router import router as api_router

# Initialize database schemas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CODEX AI Agent", version="0.1.0")

# SECURITY: Allow local React frontend (Vite defaults to port 5173) to securely call FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the API routes
app.include_router(api_router)

@app.get("/health")
async def root_health(db: Session = Depends(get_db)):
    """Primary health check endpoint verifying DB and LLM state."""
    ollama_state = await check_ollama_health()
    return {
        "status": "ok",
        "autonomy_level": settings.AUTONOMY_LEVEL,
        "database": "connected",
        "ollama": ollama_state
    }
