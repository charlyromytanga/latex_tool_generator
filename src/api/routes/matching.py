"""Matching API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks

from api.common import api_error, get_config, get_database
from orchestration.matching import compute_matching_for_offer


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
