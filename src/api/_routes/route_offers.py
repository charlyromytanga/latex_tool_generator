"""Offers API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from api._run.common import LOGGER, api_error, get_config, get_database, repo_root, safe_json_loads
from api._run.engine_offer import OfferCreateRequest, OfferDetailsResponse
from db_orchestration.ingest import OfferIngestionOrchestrator


from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks

from api._run.common import api_error, get_config, get_database
from api._run.engine_offer.engine_matching_score import compute_matching_for_offer


router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferDetailsResponse, status_code=201)
def create_offer(payload: OfferCreateRequest) -> OfferDetailsResponse:
    LOGGER.info(f"Payload reçu pour création d'offre : {payload.json()}")
    try:
        root = repo_root()
        temp_dir = root / "runs" / "tmp" / "api_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"offer_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
        temp_offer_path = temp_dir / file_name
        temp_offer_path.write_text(payload.offer_input, encoding="utf-8")

        config = get_config()
        orchestrator = OfferIngestionOrchestrator(config)
        result = orchestrator.run_from_file(temp_offer_path)

        return OfferDetailsResponse(
            offer_id=str(result["offer_id"]),
            score=0.0,
            formations=[],
            experiences=[],
            projets=[],
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
        formations, experiences, projets = [], [], []
        for row in matching_rows:
            item = dict(row)
            normalized = {
                "id": item["target_id"],
                "score": float(item["match_score"]),
                "reasoning": str(item["reasoning"])
            }
            if item["match_type"] == "formation":
                formations.append(normalized)
            elif item["match_type"] == "experience":
                experiences.append(normalized)
            elif item["match_type"] == "project":
                projets.append(normalized)

        scores = [float(e["score"]) for e in formations + experiences + projets if isinstance(e.get("score"), (int, float))]
        score = round(float(sum(scores)) / len(scores), 4) if scores else 0.0

        return OfferDetailsResponse(
            offer_id=str(offer_row["offer_id"]),
            score=score,
            formations=formations,
            experiences=experiences,
            projets=projets,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while fetching offer", exc=exc) from exc


router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/{offer_id}")
def get_matching(offer_id: str, threshold: float = 0.0, limit: int = 10) -> dict[str, object]:
    try:
        if threshold < 0.0 or threshold > 1.0:
            raise api_error(422, "threshold must be between 0.0 and 1.0")
        if limit < 1 or limit > 100:
            raise api_error(422, "limit must be between 1 and 100")

        config = get_config()
        database = get_database()
        offer_exists = database.fetch_scalar(
            "SELECT 1 FROM offers_raw WHERE offer_id = :offer_id",
            {"offer_id": offer_id},
        )
        if offer_exists is None:
            raise api_error(404, f"Offer not found: {offer_id}")

        rows = database.fetch_all(
            """
            SELECT match_type, exp_id, project_id, match_score, reasoning, model_version, computed_at
            FROM matching_scores
            WHERE offer_id = :offer_id AND match_score >= :threshold
            ORDER BY match_score DESC
            LIMIT :limit
            """,
            {"offer_id": offer_id, "threshold": threshold, "limit": limit},
        )

        formation_rows = database.fetch_all(
            """
            SELECT formation_id, match_score, reasoning, model_version, computed_at
            FROM formation_matching_scores
            WHERE offer_id = :offer_id AND match_score >= :threshold
            ORDER BY match_score DESC
            LIMIT :limit
            """,
            {"offer_id": offer_id, "threshold": threshold, "limit": limit},
        )

        experiences: list[dict[str, object]] = []
        projects: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            rank = len(experiences) + 1 if item["match_type"] == "experience" else len(projects) + 1
            normalized = {
                "rank": rank,
                "score": float(item["match_score"]),
                "reasoning": str(item["reasoning"]),
                "computed_at": item["computed_at"],
                "model_version": item["model_version"],
            }
            if item["match_type"] == "experience":
                normalized["exp_id"] = item["exp_id"]
                experiences.append(normalized)
            else:
                normalized["project_id"] = item["project_id"]
                projects.append(normalized)

        formations = [
            {
                "formation_id": row["formation_id"],
                "score": float(row["match_score"]),
                "reasoning": row["reasoning"],
                "computed_at": row["computed_at"],
                "model_version": row["model_version"],
            }
            for row in formation_rows
        ]

        all_scores: list[float] = []
        for item in experiences + projects:
            score_value = item.get("score")
            if isinstance(score_value, (int, float)):
                all_scores.append(float(score_value))
        overall_confidence = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0
        computed_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

        return {
            "offer_id": offer_id,
            "matching_computed_at": computed_at,
            "model_version": config.model_version,
            "overall_confidence": overall_confidence,
            "experiences": experiences,
            "projects": projects,
            "formations": formations,
        }
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise api_error(500, "Unexpected error while computing matching", exc=exc) from exc


@router.get("/semantic/{offer_id}")
def get_semantic_matching(offer_id: str, top_k: int = 5) -> dict:
    """
    Calcule dynamiquement le matching sémantique entre les mots-clés de l'offre et toutes les formations, expériences et projets.
    """
    database = get_database()
    result = compute_matching_for_offer(database, offer_id, top_k=top_k)
    return result


@router.post("/semantic/{offer_id}/persist")
def persist_semantic_matching(
    offer_id: str, top_k: int = 5, background_tasks: BackgroundTasks = None
) -> dict:
    """
    Calcule et insère les scores de matching sémantique pour l'offre dans la base (formations, expériences, projets).
    """
    database = get_database()
    # Exécution en tâche de fond si background_tasks fourni
    if background_tasks:
        background_tasks.add_task(
            compute_matching_for_offer, database, offer_id, top_k, True
        )
        return {"status": "processing", "offer_id": offer_id}
    else:
        result = compute_matching_for_offer(database, offer_id, top_k=top_k, persist=True)
        return result

