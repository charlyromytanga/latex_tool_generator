"""Offers API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.common import LOGGER, api_error, get_config, get_database, repo_root, safe_json_loads
from models.offer import OfferCreateRequest, OfferDetailsResponse, OfferResponse
from orchestration.ingest import OfferIngestionOrchestrator


router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferResponse, status_code=201)
def create_offer(payload: OfferCreateRequest) -> OfferResponse:
    LOGGER.info(f"Payload reçu pour création d'offre : {payload.json()}")
    try:
        root = repo_root()
        temp_dir = root / "runs" / "tmp" / "api_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_name = payload.source_file or f"offer_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
        temp_offer_path = temp_dir / file_name
        temp_offer_path.write_text(payload.markdown_content, encoding="utf-8")

        config = get_config()
        orchestrator = OfferIngestionOrchestrator(config)
        result = orchestrator.run_from_file(temp_offer_path)

        return OfferResponse(
            status="ingested",
            offer_id=str(result["offer_id"]),
            company_name=str(result["company_name"]),
            tier=str(result["tier"]),
            country=str(result["country"]),
            sections_detected={
                "company": str(result["company_name"]),
                "tier": str(result["tier"]),
                "country": str(result["country"]),
            },
        )
    except FileNotFoundError as exc:
        raise api_error(400, f"Invalid source file: {exc}", exc=exc) from exc
    except ValueError as exc:
        raise api_error(400, f"Invalid Markdown format: {exc}", exc=exc) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error during offer ingestion", exc=exc) from exc



@router.get("/{offer_id}", response_model=OfferDetailsResponse)
def get_offer(offer_id: str) -> OfferDetailsResponse:
    try:
        config = get_config()
        database = get_database()
        offer_row = database.fetch_one(
            "SELECT offer_id, offer_text, metadata_json, entities_json, keywords_json, created_at FROM offers WHERE offer_id = :offer_id",
            {"offer_id": offer_id},
        )
        if offer_row is None:
            raise api_error(404, f"Offer not found: {offer_id}")

        # Extraction des champs JSON
        metadata = safe_json_loads(offer_row.get("metadata_json", "{}"), fallback={})
        entities = safe_json_loads(offer_row.get("entities_json", "[]"), fallback=[])
        keywords = safe_json_loads(offer_row.get("keywords_json", "[]"), fallback=[])

        # Matching
        matching_rows = database.fetch_all(
            """
            SELECT match_type, target_id, match_score, reasoning
            FROM matching_scores
            WHERE offer_id = :offer_id
            ORDER BY match_score DESC
            LIMIT 10
            """,
            {"offer_id": offer_id},
        )
        top_formations, top_experiences, top_projects = [], [], []
        for row in matching_rows:
            item = dict(row)
            normalized = {
                "score": float(item["match_score"]),
                "reasoning": str(item["reasoning"]),
                "target_id": item["target_id"]
            }
            if item["match_type"] == "formation":
                top_formations.append(normalized)
            elif item["match_type"] == "experience":
                top_experiences.append(normalized)
            elif item["match_type"] == "project":
                top_projects.append(normalized)

        scores = [float(e["score"]) for e in top_formations + top_experiences + top_projects if isinstance(e.get("score"), (int, float))]
        confidence = round(float(sum(scores)) / len(scores), 4) if scores else 0.0

        recommendation = "SKIP"
        if confidence >= getattr(config, "go_threshold", 0.8):
            recommendation = "GO_TO_LEVEL3"
        elif confidence >= getattr(config, "review_threshold", 0.5):
            recommendation = "REVIEW"

        return OfferDetailsResponse(
            offer_id=str(offer_row["offer_id"]),
            company_name=metadata.get("company_name", ""),
            tier=metadata.get("tier", ""),
            country=metadata.get("country", ""),
            raw_text=str(offer_row["offer_text"]),
            sections={"entities": entities},
            keywords_extracted=keywords,
            matching_results={
                "confidence": confidence,
                "top_formations": top_formations,
                "top_experiences": top_experiences,
                "top_projects": top_projects,
            },
            recommendation=recommendation,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while fetching offer", exc=exc) from exc
