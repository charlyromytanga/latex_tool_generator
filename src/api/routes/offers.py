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
            "SELECT offer_id, company_name, tier, country, raw_text, sections_json FROM offers_raw WHERE offer_id = :offer_id",
            {"offer_id": offer_id},
        )

        if offer_row is None:
            raise api_error(404, f"Offer not found: {offer_id}")

        keywords_row = database.fetch_one(
            "SELECT keywords_json, model_version, extraction_timestamp FROM offer_keywords WHERE offer_id = :offer_id ORDER BY extraction_timestamp DESC LIMIT 1",
            {"offer_id": offer_id},
        )

        matching_rows = database.fetch_all(
            """
            SELECT match_type, exp_id, project_id, match_score, reasoning
            FROM matching_scores
            WHERE offer_id = :offer_id
            ORDER BY match_score DESC
            LIMIT 10
            """,
            {"offer_id": offer_id},
        )

        response = dict(offer_row)
        sections = safe_json_loads(response.pop("sections_json", "{}"), fallback={})
        keywords = (
            safe_json_loads(str(keywords_row["keywords_json"]), fallback={}) if keywords_row else None
        )

        top_experiences: list[dict[str, object]] = []
        top_projects: list[dict[str, object]] = []
        for row in matching_rows:
            item = dict(row)
            normalized = {
                "score": float(item["match_score"]),
                "reasoning": str(item["reasoning"]),
            }
            if item["match_type"] == "experience":
                normalized["exp_id"] = item["exp_id"]
                top_experiences.append(normalized)
            else:
                normalized["project_id"] = item["project_id"]
                top_projects.append(normalized)

        scores: list[float] = []
        for entry in top_experiences + top_projects:
            score_value = entry.get("score")
            if isinstance(score_value, (int, float)):
                scores.append(float(score_value))
        confidence = round(float(sum(scores)) / len(scores), 4) if scores else 0.0

        recommendation = "SKIP"
        if confidence >= config.go_threshold:
            recommendation = "GO_TO_LEVEL3"
        elif confidence >= config.review_threshold:
            recommendation = "REVIEW"

        return OfferDetailsResponse(
            offer_id=str(response["offer_id"]),
            company_name=str(response["company_name"]),
            tier=str(response["tier"]),
            country=str(response["country"]),
            raw_text=str(response["raw_text"]),
            sections=sections,
            keywords_extracted=keywords,
            matching_results={
                "confidence": confidence,
                "top_experiences": top_experiences,
                "top_projects": top_projects,
            },
            recommendation=recommendation,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while fetching offer", exc=exc) from exc
