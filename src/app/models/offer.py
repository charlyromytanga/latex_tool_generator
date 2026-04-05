"""Offer-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OfferCreateRequest(BaseModel):
    """Payload for POST /api/offers."""

    markdown_content: str = Field(min_length=1)
    source_file: str = Field(default="api_upload.md")


class OfferResponse(BaseModel):
    """Public response for an ingested offer."""

    offer_id: str
    company_name: str
    tier: str
    country: str
