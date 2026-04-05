"""Generation-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Payload for POST /api/generate/cv_letter."""

    offer_id: str = Field(min_length=1)
    language: str = Field(default="fr")
    force: bool = False


class GenerationStatusResponse(BaseModel):
    """Minimal status for generation polling endpoint."""

    status: str
    generation_id: str
