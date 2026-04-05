"""Compatibility wrapper for generation routes."""

from app.api.common import open_connection as get_db_connection
from app.api.routes.generate import router

__all__ = ["router", "get_db_connection"]
