"""FastAPI routers for the app package."""

from .route_generate import (
	router as generate_router,
)
from .route_offers import router as offer_router

__all__ = [
	"offer_router",
	"generate_router",
]
