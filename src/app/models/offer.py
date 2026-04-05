"""Offer-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OfferCreateRequest(BaseModel):
    """Payload for POST /api/offers."""

    markdown_content: str = Field(min_length=1)
    source_file: str = Field(default="api_upload.md")
    ingestion_date: str | None = None


class OfferResponse(BaseModel):
    """Public response for an ingested offer."""

    status: str = "ingested"
    offer_id: str
    company_name: str
    tier: str
    country: str
    sections_detected: dict[str, object] = Field(default_factory=dict)


class OfferDetailsResponse(BaseModel):
    """Detailed offer payload returned by GET /api/offers/{offer_id}."""

    offer_id: str
    company_name: str
    tier: str
    country: str
    raw_text: str
    sections: dict[str, object] = Field(default_factory=dict)
    keywords_extracted: dict[str, object] | None = None
    matching_results: dict[str, object] | None = None
    recommendation: str = "REVIEW"
