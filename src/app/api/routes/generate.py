"""Generation API routes."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.common import api_error, get_database, repo_root, safe_json_loads
from app.models.generation import (
    GenerationRequest,
    GenerationStatusResponse,
    IntegrationSubmitRequest,
)


router = APIRouter(prefix="/generate", tags=["generation"])
preview_router = APIRouter(prefix="/preview", tags=["preview"])
download_router = APIRouter(prefix="/download", tags=["download"])
integrate_router = APIRouter(prefix="/integrate", tags=["integration"])


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

        generation_id = f"gen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
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
                "generation_timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
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


@router.get("/{generation_id}", response_model=GenerationStatusResponse)
def get_generation_status(generation_id: str) -> GenerationStatusResponse:
    try:
        database = get_database()
        row = database.fetch_one(
            """
            SELECT generation_id, offer_id, status, artifact_path, top_matches_json, render_duration_ms
            FROM generations
            WHERE generation_id = :generation_id
            """,
            {"generation_id": generation_id},
        )

        if row is None:
            raise api_error(404, f"Generation not found: {generation_id}")

        db_status = str(row["status"])
        status = "rendering" if db_status == "pending" else "completed" if db_status == "success" else "failed"
        progress = 75 if status == "rendering" else 100 if status == "completed" else 0
        message = "Rendering LaTeX to PDF..." if status == "rendering" else "Generation completed"

        top_matches = safe_json_loads(row["top_matches_json"], fallback={})
        return GenerationStatusResponse(
            status=status,
            generation_id=str(row["generation_id"]),
            offer_id=str(row["offer_id"]),
            progress=progress,
            message=message,
            render_duration_ms=int(row["render_duration_ms"] or 0),
            used_experiences=list(top_matches.get("custom_experiences_ids", [])) if isinstance(top_matches, dict) else [],
            used_projects=list(top_matches.get("custom_projects_ids", [])) if isinstance(top_matches, dict) else [],
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while polling generation", exc=exc) from exc


@preview_router.get("/{generation_id}")
def preview_generation(generation_id: str) -> dict[str, object]:
    try:
        database = get_database()
        row = database.fetch_one(
            "SELECT generation_id, artifact_path FROM generations WHERE generation_id = :generation_id",
            {"generation_id": generation_id},
        )

        if row is None:
            raise api_error(404, f"Generation not found: {generation_id}")

        artifact_path = row["artifact_path"]
        if artifact_path:
            path = Path(str(artifact_path))
            if not path.is_absolute():
                path = repo_root() / path
            if path.exists() and path.is_file():
                encoded = base64.b64encode(path.read_bytes()).decode("ascii")
                return {
                    "generation_id": generation_id,
                    "artifacts": {
                        "cv": {
                            "format": "base64_pdf",
                            "pages": [encoded],
                            "page_count": 1,
                        }
                    },
                }

        # Safe fallback while real PDF preview conversion is pending.
        return {
            "generation_id": generation_id,
            "artifacts": {
                "cv": {
                    "format": "base64_png",
                    "pages": [],
                    "page_count": 0,
                },
                "letter": {
                    "format": "base64_png",
                    "pages": [],
                    "page_count": 0,
                },
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while preparing preview", exc=exc) from exc


@download_router.get("/{generation_id}/{artifact_type}")
def download_artifact(generation_id: str, artifact_type: str) -> FileResponse:
    try:
        if artifact_type not in {"cv", "letter"}:
            raise api_error(422, "artifact_type must be one of: cv, letter")

        database = get_database()
        row = database.fetch_one(
            "SELECT artifact_path FROM generations WHERE generation_id = :generation_id AND channel_type = :artifact_type ORDER BY generation_timestamp DESC LIMIT 1",
            {"generation_id": generation_id, "artifact_type": artifact_type},
        )

        if row is None or row["artifact_path"] is None:
            raise api_error(404, f"Artifact not found for generation={generation_id} type={artifact_type}")

        path = Path(str(row["artifact_path"]))
        if not path.is_absolute():
            path = repo_root() / path
        if not path.exists() or not path.is_file():
            raise api_error(404, f"Artifact file missing: {path}")

        return FileResponse(path=str(path), media_type="application/pdf", filename=path.name)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while downloading artifact", exc=exc) from exc


@integrate_router.post("/submit", status_code=202)
def integrate_submit(payload: IntegrationSubmitRequest) -> dict[str, object]:
    try:
        # Stub endpoint aligned with API spec; external adapters can plug in later.
        return {
            "status": "submitted",
            "generation_id": payload.generation_id,
            "integration": payload.integration,
            "offer_url": payload.offer_url,
            "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "metadata": payload.metadata,
        }
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while submitting integration", exc=exc) from exc
