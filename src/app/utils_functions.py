"""Shared utilities and API input/output classes for Streamlit UI."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field


class OfferCreateInput(BaseModel):
    """Input payload for offer creation endpoint."""

    markdown_content: str = Field(min_length=1)
    source_file: str = Field(default="streamlit_input.md")


class OfferCreateOutput(BaseModel):
    """Output payload from offer creation endpoint."""

    offer_id: str
    company_name: str
    tier: str
    country: str


class OfferDetailsOutput(BaseModel):
    """Output payload for offer details endpoint."""

    offer_id: str
    company_name: str
    tier: str
    country: str
    raw_text: str | None = None
    sections: dict[str, Any] = Field(default_factory=dict)
    keywords_extracted: dict[str, Any] | None = None


class MatchingOutput(BaseModel):
    """Output payload for matching endpoint."""

    offer_id: str
    overall_confidence: float = 0.0
    experiences: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    formations: list[dict[str, Any]] = Field(default_factory=list)


class GenerationInput(BaseModel):
    """Input payload for generation endpoint."""

    offer_id: str = Field(min_length=1)
    language: str = Field(default="fr")
    force: bool = False


class GenerationOutput(BaseModel):
    """Output payload from generation start/status endpoints."""

    status: str
    generation_id: str


class AppSettings(BaseModel):
    """UI settings stored in session state."""

    api_base_url: str = os.environ.get("API_URL", "http://localhost:8000")
    theme: str = "light"
    default_language: str = "fr"
    threshold: float = 0.0


class SessionPayload(BaseModel):
    """Session state model used across pages."""

    offer_id: str = ""
    generation_id: str = ""
