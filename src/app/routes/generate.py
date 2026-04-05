"""Generation API routes."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models.generation import GenerationRequest, GenerationStatusResponse
from orchestration.config import OrchestrationConfig


router = APIRouter(prefix="/generate", tags=["generation"])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@router.post("/cv_letter", response_model=GenerationStatusResponse, status_code=202)
def generate_cv_letter(payload: GenerationRequest) -> GenerationStatusResponse:
    root = _repo_root()
    config = OrchestrationConfig.from_repo_root(root)

    generation_id = f"gen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    sql = """
    INSERT INTO generations (
        generation_id,
        offer_id,
        channel_type,
        language,
        status,
        artifact_path,
        generation_timestamp,
        top_matches_json,
        render_duration_ms,
        error_message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        with sqlite3.connect(config.db_path) as conn:
            conn.execute(
                sql,
                (
                    generation_id,
                    payload.offer_id,
                    "cv",
                    payload.language,
                    "success",
                    None,
                    datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    "[]",
                    0,
                    None,
                ),
            )
            conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GenerationStatusResponse(status="generation_in_progress", generation_id=generation_id)


@router.get("/{generation_id}", response_model=GenerationStatusResponse)
def get_generation_status(generation_id: str) -> GenerationStatusResponse:
    root = _repo_root()
    config = OrchestrationConfig.from_repo_root(root)

    with sqlite3.connect(config.db_path) as conn:
        row = conn.execute(
            "SELECT status FROM generations WHERE generation_id = ?",
            (generation_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Generation not found: {generation_id}")

    status = str(row[0])
    return GenerationStatusResponse(status=status, generation_id=generation_id)
