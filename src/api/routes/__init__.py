"""FastAPI routers for the app package."""

from .generate import (
	download_router,
	integrate_router,
	preview_router,
	router as generate_router,
)
from .matching import router as matching_router
from .offers import router as offers_router

__all__ = [
	"offers_router",
	"matching_router",
	"generate_router",
	"preview_router",
	"download_router",
	"integrate_router",
]
