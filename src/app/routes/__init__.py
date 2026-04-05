"""FastAPI routers for the app package."""

from .generate import router as generate_router
from .matching import router as matching_router
from .offers import router as offers_router

__all__ = ["offers_router", "matching_router", "generate_router"]
