"""HTTP client wrapper for Recruitment API with robust error handling."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.utils_functions import (
    GenerationInput,
    GenerationOutput,
    MatchingOutput,
    OfferCreateInput,
    OfferCreateOutput,
    OfferDetailsOutput,
)


LOGGER = logging.getLogger(__name__)


class ApiClientError(RuntimeError):
    """Raised when an API call fails."""


class RecruitmentApiClient:
    """Thin API client for Streamlit pages."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def create_offer(self, payload: OfferCreateInput) -> OfferCreateOutput:
        data = self._post("/api/offers", payload.model_dump())
        return OfferCreateOutput.model_validate(data)

    def get_offer(self, offer_id: str) -> OfferDetailsOutput:
        data = self._get(f"/api/offers/{offer_id}")
        return OfferDetailsOutput.model_validate(data)

    def get_matching(self, offer_id: str, threshold: float, limit: int = 10) -> MatchingOutput:
        data = self._get(
            f"/api/matching/{offer_id}",
            params={"threshold": threshold, "limit": limit},
        )
        return MatchingOutput.model_validate(data)

    def generate_cv_letter(self, payload: GenerationInput) -> GenerationOutput:
        data = self._post("/api/generate/cv_letter", payload.model_dump())
        return GenerationOutput.model_validate(data)

    def get_generation_status(self, generation_id: str) -> GenerationOutput:
        data = self._get(f"/api/generate/{generation_id}")
        return GenerationOutput.model_validate(data)

    def health(self) -> dict[str, Any]:
        return self._get("/api/health")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            LOGGER.exception(f"GET {url} failed: {exc}")
            raise ApiClientError from exc

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            LOGGER.exception(f"POST {url} failed: {exc}")
            raise ApiClientError from exc
