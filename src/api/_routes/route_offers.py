"""Offers API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from api._run.common import LOGGER, api_error, get_config, get_database, repo_root, safe_json_loads
from api._run.engine_offer import OfferCreateRequest, OfferDetailsResponse
from db_orchestration.ingest import OfferIngestionOrchestrator

from api._run.common import api_error, get_config, get_database


router = APIRouter(prefix="/offer", tags=["offer"])


@router.post("", response_model=OfferDetailsResponse, status_code=200)
def create_offer(payload: OfferCreateRequest) -> OfferDetailsResponse:
    LOGGER.info(f"Payload reçu pour création d'offre : {payload.model_dump_json()}")
    try:
        root = repo_root()
        temp_dir = root / "runs" / "tmp" / "api_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"offer_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        temp_offer_path = temp_dir / file_name
        temp_offer_path.write_text(payload.offer_input, encoding="utf-8")

        config = get_config()
        orchestrator = OfferIngestionOrchestrator(config)
        result: Dict[str, object] = orchestrator.run_from_payload(
            payload.offer_input,
            payload.company,
            payload.location,
            payload.offer_title,
            temp_offer_path
        )

        offer_id = str(result["offer_id"])
        keywords = result["keywords"]

        return OfferDetailsResponse(
            offer_id=offer_id,
            keywords=keywords,
        )

    except FileNotFoundError as exc:
        raise api_error(400, f"Invalid source file: {exc}", exc=exc) from exc
    except ValueError as exc:
        raise api_error(400, f"Invalid offer format: {exc}", exc=exc) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error during offer ingestion", exc=exc) from exc



@router.get("/{offer_id}", response_model=OfferDetailsResponse)
def get_offer(offer_id: str) -> OfferDetailsResponse:
    try:
        database = get_database()
        # Vérifier l'existence de l'offre (sinon 404)
        offer_row = database.fetch_one(
            "SELECT offer_id, keywords FROM offers WHERE offer_id = :offer_id",
            {
                "offer_id": offer_id,
                "keywords": "keywords"
            },
        )
        if offer_row is None:
            raise api_error(404, f"Offer not found: {offer_id}")

        return OfferDetailsResponse(
            offer_id=offer_id,
            keywords=offer_row["keywords"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise api_error(500, "Unexpected error while fetching offer", exc=exc) from exc