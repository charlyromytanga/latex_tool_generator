"""Offers API routes."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.offer import OfferCreateRequest, OfferResponse
from orchestration.config import OrchestrationConfig
from orchestration.ingest import OfferIngestionOrchestrator


router = APIRouter(prefix="/offers", tags=["offers"])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@router.post("", response_model=OfferResponse, status_code=201)
def create_offer(payload: OfferCreateRequest) -> OfferResponse:
    root = _repo_root()
    temp_dir = root / "runs" / "tmp" / "api_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"offer_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
    temp_offer_path = temp_dir / file_name
    temp_offer_path.write_text(payload.markdown_content, encoding="utf-8")

    config = OrchestrationConfig.from_repo_root(root)
    orchestrator = OfferIngestionOrchestrator(config)
    result = orchestrator.run_from_file(temp_offer_path)

    return OfferResponse(
        offer_id=str(result["offer_id"]),
        company_name=str(result["company_name"]),
        tier=str(result["tier"]),
        country=str(result["country"]),
    )


@router.get("/{offer_id}")
def get_offer(offer_id: str) -> dict[str, object]:
    root = _repo_root()
    config = OrchestrationConfig.from_repo_root(root)

    with sqlite3.connect(config.db_path) as conn:
        conn.row_factory = sqlite3.Row
        offer_row = conn.execute(
            "SELECT offer_id, company_name, tier, country, raw_text, sections_json FROM offers_raw WHERE offer_id = ?",
            (offer_id,),
        ).fetchone()

        if offer_row is None:
            raise HTTPException(status_code=404, detail=f"Offer not found: {offer_id}")

        keywords_row = conn.execute(
            "SELECT keywords_json, model_version, extraction_timestamp FROM offer_keywords WHERE offer_id = ? ORDER BY extraction_timestamp DESC LIMIT 1",
            (offer_id,),
        ).fetchone()

    response = dict(offer_row)
    response["sections"] = json.loads(str(response.pop("sections_json")))
    response["keywords_extracted"] = (
        json.loads(str(keywords_row["keywords_json"])) if keywords_row else None
    )
    return response
