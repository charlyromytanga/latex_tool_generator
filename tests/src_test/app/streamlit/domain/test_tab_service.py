"""Unit tests for app.streamlit.domain.tab_service module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.streamlit.domain.tab_service import TabService
from app.streamlit.services.api_client import ApiClientError
from app.streamlit.utils_functions import OfferCreateInput


class TestTabService:
    """Tests for TabService class."""

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client."""
        return Mock()

    @pytest.fixture
    def service(self, mock_api_client):
        """Create TabService instance with mock client."""
        return TabService(api_client=mock_api_client)

    def test_service_initialization(self, service, mock_api_client):
        """Test TabService is properly initialized."""
        assert service.api_client == mock_api_client

    def test_submit_offer_success(self, service, mock_api_client):
        """Test successful offer submission."""
        mock_api_client.create_offer.return_value = {
            "offer_id": "offer-123",
            "title": "Developer"
        }
        
        input_data = OfferCreateInput(markdown_content="# Test Offer")
        result = service.submit_offer(input_data)
        
        assert result is not None
        mock_api_client.create_offer.assert_called_once()

    def test_submit_offer_api_error(self, service, mock_api_client):
        """Test offer submission with API error."""
        mock_api_client.create_offer.side_effect = ApiClientError("Connection failed")
        
        input_data = OfferCreateInput(markdown_content="# Test Offer")
        
        with pytest.raises(ApiClientError):
            service.submit_offer(input_data)

    def test_fetch_offer_success(self, service, mock_api_client):
        """Test successful offer fetch."""
        mock_api_client.get_offer.return_value = {
            "offer_id": "offer-123",
            "title": "Senior Developer",
            "company": "TechCorp"
        }
        
        result = service.fetch_offer("offer-123")
        
        assert result is not None
        assert result["title"] == "Senior Developer"

    def test_fetch_offer_not_found(self, service, mock_api_client):
        """Test fetching non-existent offer."""
        mock_api_client.get_offer.side_effect = ApiClientError("Not found", status_code=404)
        
        with pytest.raises(ApiClientError):
            service.fetch_offer("nonexistent")

    def test_fetch_matching_success(self, service, mock_api_client):
        """Test successful matching fetch."""
        mock_api_client.get_matching.return_value = {
            "offer_id": "offer-123",
            "overall_confidence": 0.85,
            "experience_matches": [
                {"entity_id": "exp-1", "match_score": 0.9}
            ],
            "project_matches": [],
            "formation_matches": []
        }
        
        result = service.fetch_matching("offer-123")
        
        assert result is not None
        assert result["overall_confidence"] == 0.85

    def test_start_generation_success(self, service, mock_api_client):
        """Test successful generation start."""
        mock_api_client.generate_cv_letter.return_value = {
            "generation_id": "gen-123",
            "status": "processing"
        }
        
        result = service.start_generation("offer-123", "en")
        
        assert result is not None
        assert "generation_id" in result

    def test_read_generation_status_success(self, service, mock_api_client):
        """Test successful generation status read."""
        mock_api_client.get_generation_status.return_value = {
            "generation_id": "gen-123",
            "status": "completed",
            "cv_content": "# CV"
        }
        
        result = service.read_generation_status("gen-123")
        
        assert result is not None
        assert result["status"] == "completed"

    def test_read_generation_status_processing(self, service, mock_api_client):
        """Test generation status shows processing."""
        mock_api_client.get_generation_status.return_value = {
            "generation_id": "gen-123",
            "status": "processing"
        }
        
        result = service.read_generation_status("gen-123")
        
        assert result is not None
        assert result["status"] == "processing"

    def test_service_error_logging(self, service, mock_api_client):
        """Test that errors are logged."""
        mock_api_client.create_offer.side_effect = Exception("Test error")
        
        input_data = OfferCreateInput(markdown_content="# Test")
        
        with pytest.raises(Exception):
            service.submit_offer(input_data)

    def test_multiple_operations_sequence(self, service, mock_api_client):
        """Test sequence of operations."""
        # Mock responses
        mock_api_client.create_offer.return_value = {"offer_id": "offer-456"}
        mock_api_client.get_offer.return_value = {"offer_id": "offer-456", "title": "Job"}
        mock_api_client.get_matching.return_value = {
            "offer_id": "offer-456",
            "overall_confidence": 0.75
        }
        
        # Submit
        submit_result = service.submit_offer(OfferCreateInput(markdown_content="# Job"))
        assert submit_result is not None
        
        # Fetch
        fetch_result = service.fetch_offer("offer-456")
        assert fetch_result is not None
        
        # Get matching
        match_result = service.fetch_matching("offer-456")
        assert match_result is not None

    def test_api_client_dependency_injection(self):
        """Test that API client can be injected."""
        custom_client = Mock()
        service = TabService(api_client=custom_client)
        
        assert service.api_client == custom_client
