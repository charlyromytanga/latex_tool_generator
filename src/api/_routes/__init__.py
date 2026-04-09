"""FastAPI routers for the app package."""

from .route_generate import (
	download_router,
	integrate_router,
	preview_router,
	router as generate_router,
)
from .route_offers import router as offers_router

__all__ = [
	"offers_router",
	"generate_router",
	"preview_router",
	"download_router",
	"integrate_router",
]
