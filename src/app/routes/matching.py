"""Matching API routes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter

from orchestration.config import OrchestrationConfig


router = APIRouter(prefix="/matching", tags=["matching"])


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@router.get("/{offer_id}")
def get_matching(offer_id: str, threshold: float = 0.0, limit: int = 10) -> dict[str, object]:
    root = _repo_root()
    config = OrchestrationConfig.from_repo_root(root)

    with sqlite3.connect(config.db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT match_type, exp_id, project_id, match_score, reasoning, model_version, computed_at
            FROM matching_scores
            WHERE offer_id = ? AND match_score >= ?
            ORDER BY match_score DESC
            LIMIT ?
            """,
            (offer_id, threshold, limit),
        ).fetchall()

        formation_rows = conn.execute(
            """
            SELECT formation_id, match_score, reasoning, model_version, computed_at
            FROM formation_matching_scores
            WHERE offer_id = ? AND match_score >= ?
            ORDER BY match_score DESC
            LIMIT ?
            """,
            (offer_id, threshold, limit),
        ).fetchall()

    experiences: list[dict[str, object]] = []
    projects: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        if item["match_type"] == "experience":
            experiences.append(item)
        else:
            projects.append(item)

    formations = [dict(row) for row in formation_rows]
    all_scores = [float(item["match_score"]) for item in experiences + projects]
    overall_confidence = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0

    return {
        "offer_id": offer_id,
        "overall_confidence": overall_confidence,
        "experiences": experiences,
        "projects": projects,
        "formations": formations,
    }
