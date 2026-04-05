"""Unit tests for app.streamlit.utils_functions module."""

import pytest
from pydantic import ValidationError
from app.streamlit.utils_functions import (
    OfferCreateInput,
    OfferCreateOutput,
    OfferDetailsOutput,
    MatchingOutput,
    GenerationInput,
    GenerationOutput,
    AppSettings,
    SessionPayload,
)


class TestOfferCreateInput:
    """Tests for OfferCreateInput model."""

    def test_valid_offer_input(self):
        """Test creating valid offer input."""
        input_data = {
            "markdown_content": "# Senior Developer\n\n## Description\nTest position"
        }
        offer_input = OfferCreateInput(**input_data)
        assert offer_input.markdown_content == input_data["markdown_content"]

    def test_offer_input_validation_empty(self):
        """Test that empty markdown is invalid."""
        with pytest.raises(ValidationError):
            OfferCreateInput(markdown_content="")


class TestOfferDetailOutput:
    """Tests for OfferDetailsOutput model."""

    def test_valid_offer_details(self):
        """Test creating valid offer details."""
        details = {
            "offer_id": "offer-123",
            "title": "Senior Developer",
            "company": "TechCorp",
            "description": "We are hiring...",
            "keywords": ["python", "fastapi", "backend"],
            "created_at": "2025-04-05T10:00:00Z"
        }
        output = OfferDetailsOutput(**details)
        assert output.offer_id == "offer-123"
        assert output.title == "Senior Developer"
        assert len(output.keywords) == 3


class TestMatchingOutput:
    """Tests for MatchingOutput model."""

    def test_valid_matching_output(self):
        """Test creating valid matching output."""
        data = {
            "offer_id": "offer-123",
            "overall_confidence": 0.85,
            "experience_matches": [
                {"entity_id": "exp-1", "match_score": 0.9, "entity_type": "experience"}
            ],
            "project_matches": [
                {"entity_id": "proj-1", "match_score": 0.75, "entity_type": "project"}
            ],
            "formation_matches": []
        }
        output = MatchingOutput(**data)
        assert output.overall_confidence == 0.85
        assert len(output.experience_matches) > 0

    def test_matching_output_empty_matches(self):
        """Test matching output with no matches."""
        data = {
            "offer_id": "offer-456",
            "overall_confidence": 0.0,
            "experience_matches": [],
            "project_matches": [],
            "formation_matches": []
        }
        output = MatchingOutput(**data)
        assert output.overall_confidence == 0.0


class TestGenerationModels:
    """Tests for generation-related models."""

    def test_generation_input_valid(self):
        """Test valid generation input."""
        input_data = {
            "offer_id": "offer-123",
            "language": "en",
            "include_cover_letter": True
        }
        gen_input = GenerationInput(**input_data)
        assert gen_input.offer_id == "offer-123"
        assert gen_input.language == "en"

    def test_generation_output_valid(self):
        """Test valid generation output."""
        output_data = {
            "generation_id": "gen-123",
            "offer_id": "offer-123",
            "status": "completed",
            "cv_content": "# CV",
            "letter_content": "# Letter",
            "created_at": "2025-04-05T10:00:00Z"
        }
        gen_output = GenerationOutput(**output_data)
        assert gen_output.generation_id == "gen-123"
        assert gen_output.status == "completed"


class TestAppSettings:
    """Tests for AppSettings model."""

    def test_app_settings_defaults(self):
        """Test app settings with defaults."""
        settings = AppSettings(
            api_base_url="http://localhost:8000",
            theme="light",
            language="en"
        )
        assert settings.api_base_url == "http://localhost:8000"
        assert settings.theme in ["light", "dark"]
        assert settings.language in ["en", "fr"]

    def test_app_settings_with_threshold(self):
        """Test app settings with custom threshold."""
        settings = AppSettings(
            api_base_url="http://localhost:8000",
            threshold=0.7
        )
        assert 0.0 <= settings.threshold <= 1.0


class TestSessionPayload:
    """Tests for SessionPayload model."""

    def test_session_payload_creation(self):
        """Test creating session payload."""
        payload = SessionPayload(
            offer_id="offer-123",
            generation_id="gen-456",
            theme="dark",
            language="fr",
            threshold=0.6
        )
        assert payload.offer_id == "offer-123"
        assert payload.generation_id == "gen-456"
        assert payload.theme == "dark"

    def test_session_payload_optional_fields(self):
        """Test session payload with minimal data."""
        payload = SessionPayload()
        assert payload.offer_id is None
        assert payload.generation_id is None
