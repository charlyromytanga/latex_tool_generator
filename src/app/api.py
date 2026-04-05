"""FastAPI application entrypoint for Recruitment Assistant V2."""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI

from app.routes import generate_router, matching_router, offers_router


app = FastAPI(
    title="Recruitment Assistant API",
    version="0.1.0",
    description="V2 API for offer ingestion, matching and generation orchestration.",
)

app.include_router(offers_router, prefix="/api")
app.include_router(matching_router, prefix="/api")
app.include_router(generate_router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health() -> dict[str, object]:
    """Lightweight health endpoint used for local checks and deployment probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "db_connected": True,
        "llm_available": False,
    }
