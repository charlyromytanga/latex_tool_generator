"""Business module for Streamlit tabs (OOP use cases)."""

from __future__ import annotations

import logging

from streamlit.services.api_client import ApiClientError, RecruitmentApiClient
from streamlit.utils_functions import (
    GenerationInput,
    GenerationOutput,
    MatchingOutput,
    OfferCreateInput,
    OfferCreateOutput,
    OfferDetailsOutput,
)


LOGGER = logging.getLogger(__name__)


class TabService:
    """Use-case layer consumed by UI pages."""

    def __init__(self, api_client: RecruitmentApiClient) -> None:
        self.api_client = api_client

    def submit_offer(self, markdown_content: str) -> OfferCreateOutput:
        try:
            payload = OfferCreateInput(markdown_content=markdown_content)
            return self.api_client.create_offer(payload)
        except ApiClientError:
            LOGGER.exception("Offer submission failed")
            raise

    def fetch_offer(self, offer_id: str) -> OfferDetailsOutput:
        try:
            return self.api_client.get_offer(offer_id)
        except ApiClientError:
            LOGGER.exception("Offer fetch failed for %s", offer_id)
            raise

    def fetch_matching(self, offer_id: str, threshold: float) -> MatchingOutput:
        try:
            return self.api_client.get_matching(offer_id=offer_id, threshold=threshold)
        except ApiClientError:
            LOGGER.exception("Matching fetch failed for %s", offer_id)
            raise

    def start_generation(self, offer_id: str, language: str, force: bool) -> GenerationOutput:
        try:
            payload = GenerationInput(offer_id=offer_id, language=language, force=force)
            return self.api_client.generate_cv_letter(payload)
        except ApiClientError:
            LOGGER.exception("Generation start failed for %s", offer_id)
            raise

    def read_generation_status(self, generation_id: str) -> GenerationOutput:
        try:
            return self.api_client.get_generation_status(generation_id)
        except ApiClientError:
            LOGGER.exception("Generation status failed for %s", generation_id)
            raise
