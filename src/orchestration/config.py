"""Central configuration for V2 orchestration modules."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OrchestrationConfig:
    """Runtime settings shared across ingest, matching and generation modules."""

    db_path: Path
    schema_path: Path
    default_language: str
    review_threshold: float
    go_threshold: float
    model_version: str

    @classmethod
    def from_repo_root(cls, root: Path) -> "OrchestrationConfig":
        return cls(
            db_path=Path(os.getenv("RECRUITMENT_DB_PATH", root / "db" / "recruitment_assistant.db")),
            schema_path=Path(os.getenv("RECRUITMENT_SCHEMA_PATH", root / "db" / "schema_init.sql")),
            default_language=os.getenv("DEFAULT_LANGUAGE", "fr"),
            review_threshold=float(os.getenv("MATCH_REVIEW_THRESHOLD", "0.5")),
            go_threshold=float(os.getenv("MATCH_GO_THRESHOLD", "0.75")),
            model_version=os.getenv("LLM_MODEL_VERSION", "heuristic-v0"),
        )
