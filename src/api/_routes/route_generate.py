"""Generation API routes."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api._run.common import api_error, get_database
from api._run.engine_generation import (
    GenerationRequest,
    GenerationStatusResponse,
)


router = APIRouter(prefix="/generate", tags=["generation"])


@router.post("/cv_letter", response_model=GenerationStatusResponse, status_code=202)
def generate_cv_letter(payload: GenerationRequest) -> GenerationStatusResponse:
    try:
        database = get_database()
        offer_exists = database.fetch_scalar(
            "SELECT 1 FROM offers_raw WHERE offer_id = :offer_id",
            {"offer_id": payload.offer_id},
        )
        if offer_exists is None:
            raise api_error(404, f"Offer not found: {payload.offer_id}")

        generation_id = f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        top_matches_json = json.dumps(
            {
                "use_top_matches": payload.use_top_matches,
                "custom_experiences_ids": payload.custom_experiences_ids,
                "custom_projects_ids": payload.custom_projects_ids,
            },
            ensure_ascii=True,
        )

        database.execute(
            """
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
            ) VALUES (
                :generation_id,
                :offer_id,
                :channel_type,
                :language,
                :status,
                :artifact_path,
                :generation_timestamp,
                :top_matches_json,
                :render_duration_ms,
                :error_message
            )
            """,
            {
                "generation_id": generation_id,
                "offer_id": payload.offer_id,
                "channel_type": "cv",
                "language": payload.language,
                "status": "pending",
                "artifact_path": None,
                "generation_timestamp": datetime.now().isoformat(timespec="seconds") + "Z",
                "top_matches_json": top_matches_json,
                "render_duration_ms": 0,
                "error_message": None,
            },
        )

        return GenerationStatusResponse(
            status="generation_in_progress",
            generation_id=generation_id,
            offer_id=payload.offer_id,
            estimated_duration_seconds=30,
            message="Generation started",
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while starting generation", exc=exc) from exc

@router.get("/status/{generation_id}", response_model=GenerationStatusResponse)
def get_generation_status(generation_id: str) -> GenerationStatusResponse:
    try:
        database = get_database()
        row = database.fetch_one(
            """
            SELECT generation_id, offer_id, status, artifact_path, generation_timestamp,
                   render_duration_ms, error_message, top_matches_json
            FROM generations
            WHERE generation_id = :generation_id
            """,
            {"generation_id": generation_id},
        )
        if row is None:
            raise api_error(404, f"Generation not found: {generation_id}")

        top_matches_info = json.loads(row["top_matches_json"] or "{}")
        return GenerationStatusResponse(
            status=row["status"],
            generation_id=row["generation_id"],
            offer_id=row["offer_id"],
            estimated_duration_seconds=30,
            message=row["error_message"],
            artifacts={"artifact_path": row["artifact_path"]} if row["artifact_path"] else None,
            render_duration_ms=row["render_duration_ms"],
            used_experiences=top_matches_info.get("custom_experiences_ids", []),
            used_projects=top_matches_info.get("custom_projects_ids", []),
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while fetching generation status", exc=exc) from exc
