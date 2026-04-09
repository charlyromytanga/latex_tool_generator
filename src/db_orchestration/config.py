"""Central configuration for V2 orchestration modules."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .database import detect_database_backend, normalize_database_url


@dataclass(frozen=True)
class OrchestrationConfig:
    """Runtime settings shared across ingest, matching and generation modules."""

    database_url: str
    db_backend: str
    db_path: Path
    sqlite_schema_path: Path
    postgres_schema_path: Path
    default_language: str
    review_threshold: float
    go_threshold: float
    model_version: str

    @property
    def schema_path(self) -> Path:
        return self.postgres_schema_path if self.db_backend == "postgresql" else self.sqlite_schema_path

    @classmethod
    def from_repo_root(cls, root: Path) -> "OrchestrationConfig":
        # Centralized environment loading from repository root.
        load_dotenv(root / ".env", override=False)
        sqlite_path = Path(os.getenv("RECRUITMENT_DB_PATH", root / "db" / "recruitment_assistant.db"))
        database_url = normalize_database_url(os.getenv("DATABASE_URL"), root, sqlite_path)
        return cls(
            database_url=database_url,
            db_backend=detect_database_backend(database_url),
            db_path=sqlite_path,
            sqlite_schema_path=Path(os.getenv("RECRUITMENT_SCHEMA_PATH", root / "db" / "schema_init.sql")),
            postgres_schema_path=Path(
                os.getenv("RECRUITMENT_POSTGRES_SCHEMA_PATH", root / "db" / "schema_postgres.sql")
            ),
            default_language=os.getenv("DEFAULT_LANGUAGE", "fr"),
            review_threshold=float(os.getenv("MATCH_REVIEW_THRESHOLD", "0.5")),
            go_threshold=float(os.getenv("MATCH_GO_THRESHOLD", "0.75")),
            model_version=os.getenv("LLM_MODEL_VERSION", "heuristic-v0"),
        )
