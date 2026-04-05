"""FastAPI application entrypoint for Recruitment Assistant V2."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.common import api_error, get_database
from api.routes import (
    download_router,
    generate_router,
    integrate_router,
    matching_router,
    offers_router,
    preview_router,
)


LOGGER = logging.getLogger("app.api")


def create_app() -> FastAPI:
    """Create configured FastAPI app instance."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    api = FastAPI(
        title="Recruitment Assistant API",
        version="0.2.0",
        description="V2 API for offer ingestion, matching and generation orchestration.",
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api.include_router(offers_router, prefix="/api")
    api.include_router(matching_router, prefix="/api")
    api.include_router(generate_router, prefix="/api")
    api.include_router(preview_router, prefix="/api")
    api.include_router(download_router, prefix="/api")
    api.include_router(integrate_router, prefix="/api")

    @api.get("/api/health", tags=["health"])
    def health() -> dict[str, object]:
        """Lightweight health endpoint used for local checks and deployment probes."""
        try:
            db_connected = get_database().can_connect()
        except Exception as exc:  # pylint: disable=broad-except
            raise api_error(500, "Health check failed", exc=exc) from exc

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "db_connected": db_connected,
            "llm_available": True,
        }

    return api


app = create_app()
