"""Compatibility package forwarding to app.api.routes."""

from app.api.routes.generate import router as generate_router
from app.api.routes.matching import router as matching_router
from app.api.routes.offers import router as offers_router

__all__ = ["offers_router", "matching_router", "generate_router"]
