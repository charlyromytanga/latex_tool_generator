"""Offers API routes."""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

from api._run.common import LOGGER, api_error, get_config, get_database, repo_root, safe_json_loads
from api._run.engine_offer import OfferCreateRequest, OfferDetailsResponse
from db_orchestration.ingest import OfferIngestionOrchestrator

from api._run.common import api_error, get_config, get_database
from api._run.engine_offer import compute_matching_for_offer


router = APIRouter(prefix="/offer", tags=["offer"])


@router.post("", response_model=OfferDetailsResponse, status_code=201)
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
        result = orchestrator.run_from_file(temp_offer_path)

        offer_id = str(result["offer_id"])
        database = get_database()
        matching = compute_matching_for_offer(database, offer_id)
        formations = matching.get("formation_scores", [])
        experiences = matching.get("experience_scores", [])
        projets = matching.get("project_scores", [])
        all_scores = [f.get("max", 0.0) for f in formations] + [e.get("max", 0.0) for e in experiences] + [p.get("max", 0.0) for p in projets]
        score = round(float(sum(all_scores)) / len(all_scores), 4) if all_scores else 0.0
        return OfferDetailsResponse(
            offer_id=offer_id,
            score=score,
            formations=formations,
            experiences=experiences,
            projets=projets,
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
            "SELECT offer_id FROM offers WHERE offer_id = :offer_id",
            {"offer_id": offer_id},
        )
        if offer_row is None:
            raise api_error(404, f"Offer not found: {offer_id}")

        # Utiliser la logique centrale de matching
        matching = compute_matching_for_offer(database, offer_id)
        formations = matching.get("formation_scores", [])
        experiences = matching.get("experience_scores", [])
        projets = matching.get("project_scores", [])
        all_scores = [f.get("max", 0.0) for f in formations] + [e.get("max", 0.0) for e in experiences] + [p.get("max", 0.0) for p in projets]
        score = round(float(sum(all_scores)) / len(all_scores), 4) if all_scores else 0.0
        return OfferDetailsResponse(
            offer_id=offer_id,
            score=score,
            formations=formations,
            experiences=experiences,
            projets=projets,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise api_error(500, "Unexpected error while fetching offer", exc=exc) from exc