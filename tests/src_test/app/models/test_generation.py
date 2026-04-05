"""Unit tests for app.models.generation module."""

import pytest
from datetime import datetime
from app.models.generation import GenerationRequest, GenerationStatusResponse


class TestGenerationRequest:
    """Tests for GenerationRequest model."""

    def test_valid_generation_request(self):
        """Test creating valid generation request."""
        data = {
            "offer_id": "offer-123",
            "language": "en",
            "include_cover_letter": True
        }
        request = GenerationRequest(**data)
        assert request.offer_id == data["offer_id"]
        assert request.language == data["language"]
        assert request.include_cover_letter is True

    def test_generation_request_with_defaults(self):
        """Test generation request uses defaults."""
        data = {"offer_id": "offer-456"}
        request = GenerationRequest(**data)
        assert request.offer_id == data["offer_id"]
        assert request.language == "en"

    def test_generation_request_language_validation(self):
        """Test language must be valid."""
        with pytest.raises(ValueError):
            GenerationRequest(
                offer_id="offer-123",
                language="xx"  # Invalid language code
            )


class TestGenerationStatusResponse:
    """Tests for GenerationStatusResponse model."""

    def test_valid_generation_status_response(self):
        """Test creating valid status response."""
        data = {
            "generation_id": "gen-123",
            "offer_id": "offer-123",
            "status": "completed",
            "cv_pdf_url": "/artifacts/gen-123/cv.pdf",
            "letter_pdf_url": "/artifacts/gen-123/letter.pdf",
            "created_at": datetime.now(),
            "completed_at": datetime.now()
        }
        response = GenerationStatusResponse(**data)
        assert response.generation_id == data["generation_id"]
        assert response.status == "completed"
        assert response.cv_pdf_url is not None

    def test_generation_status_processing(self):
        """Test processing status without artifacts."""
        data = {
            "generation_id": "gen-456",
            "offer_id": "offer-456",
            "status": "processing",
            "created_at": datetime.now()
        }
        response = GenerationStatusResponse(**data)
        assert response.status == "processing"
        assert response.cv_pdf_url is None

    def test_generation_status_serialization(self):
        """Test status response can be serialized."""
        data = {
            "generation_id": "gen-789",
            "offer_id": "offer-789",
            "status": "failed",
            "error_message": "PDF generation failed",
            "created_at": datetime.now()
        }
        response = GenerationStatusResponse(**data)
        json_data = response.model_dump_json()
        assert "gen-789" in json_data
        assert "failed" in json_data
