"""Unit tests for app.models.offer module."""

import pytest
from datetime import datetime
from app.models.offer import OfferCreateRequest, OfferResponse


class TestOfferCreateRequest:
    """Tests for OfferCreateRequest model."""

    def test_valid_offer_create_request(self):
        """Test creating valid offer request."""
        data = {
            "markdown_content": "# Test Offer\n\n## Details\nTest job offer",
            "source_url": "https://example.com/offer/123"
        }
        request = OfferCreateRequest(**data)
        assert request.markdown_content == data["markdown_content"]
        assert request.source_url == data["source_url"]

    def test_offer_create_request_minimal(self):
        """Test creating offer request with minimal data."""
        data = {"markdown_content": "# Job Offer"}
        request = OfferCreateRequest(**data)
        assert request.markdown_content == data["markdown_content"]
        assert request.source_url is None

    def test_offer_create_request_validation(self):
        """Test offer request validation."""
        with pytest.raises(ValueError):
            OfferCreateRequest(markdown_content="")


class TestOfferResponse:
    """Tests for OfferResponse model."""

    def test_valid_offer_response(self):
        """Test creating valid offer response."""
        data = {
            "offer_id": "test-offer-123",
            "title": "Senior Developer",
            "company": "TechCorp",
            "description": "We are looking for...",
            "keywords": ["python", "fastapi"],
            "created_at": datetime.now(),
            "source_url": "https://example.com/offers/123"
        }
        response = OfferResponse(**data)
        assert response.offer_id == data["offer_id"]
        assert response.title == data["title"]
        assert response.company == data["company"]
        assert len(response.keywords) == 2

    def test_offer_response_serialization(self):
        """Test offer response can be serialized to JSON."""
        data = {
            "offer_id": "test-offer",
            "title": "Developer",
            "company": "Company",
            "description": "Description",
            "keywords": ["tech", "python"],
            "created_at": datetime.now(),
        }
        response = OfferResponse(**data)
        json_data = response.model_dump_json()
        assert "test-offer" in json_data
        assert "Developer" in json_data
