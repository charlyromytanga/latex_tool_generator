"""Shared helpers for API routes (logging, DB access, safety helpers)."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from db_orchestration.config import OrchestrationConfig
from db_orchestration.database import Database


LOGGER = logging.getLogger("app.api")


def repo_root() -> Path:
    """Resolve repository root from api package location."""
    return Path(__file__).resolve().parents[3]


def get_config() -> OrchestrationConfig:
    """Get orchestration config bound to repository root."""
    return OrchestrationConfig.from_repo_root(repo_root())


@lru_cache(maxsize=1)
def _get_database(database_url: str) -> Database:
    return Database(database_url)


def get_database() -> Database:
    """Return the shared runtime database accessor."""
    config = get_config()
    return _get_database(config.database_url)


def safe_json_loads(raw: Any, fallback: Any) -> Any:
    """Decode JSON string while preserving API stability on malformed values."""
    if raw is None:
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    if not isinstance(raw, str):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        LOGGER.warning("Invalid JSON payload encountered in DB field")
        return fallback


def api_error(status_code: int, detail: str, *, exc: Exception | None = None) -> HTTPException:
    """Create HTTPException with consistent logging."""
    if exc is None:
        LOGGER.error("API error status=%s detail=%s", status_code, detail)
    else:
        LOGGER.exception("API error status=%s detail=%s", status_code, detail)
    return HTTPException(status_code=status_code, detail=detail)
