"""Generation-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Payload for POST /api/generate/cv_letter."""

    offer_id: str = Field(min_length=1)
    language: str = Field(default="fr")
    force: bool = False
    use_top_matches: bool = True
    custom_experiences_ids: list[str] = Field(default_factory=list)
    custom_projects_ids: list[str] = Field(default_factory=list)


class GenerationStatusResponse(BaseModel):
    """Minimal status for generation polling endpoint."""

    status: str
    generation_id: str
    offer_id: str | None = None
    estimated_duration_seconds: int | None = None
    progress: int | None = None
    message: str | None = None
    artifacts: dict[str, object] | None = None
    render_duration_ms: int | None = None
    used_experiences: list[str] = Field(default_factory=list)
    used_projects: list[str] = Field(default_factory=list)


class IntegrationSubmitRequest(BaseModel):
    """Payload for POST /api/integrate/submit."""

    generation_id: str = Field(min_length=1)
    integration: str = Field(default="linkedin")
    offer_url: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)
