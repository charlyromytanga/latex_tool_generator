"""Unit tests for app.streamlit.services.api_client module."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import HTTPStatusError, Response
from app.streamlit.services.api_client import RecruitmentApiClient, ApiClientError
from app.streamlit.utils_functions import (
    OfferCreateInput,
    OfferDetailsOutput,
    MatchingOutput,
    GenerationInput,
    GenerationOutput,
)


class TestApiClientError:
    """Tests for ApiClientError exception."""

    def test_api_client_error_creation(self):
        """Test creating API client error."""
        error = ApiClientError("Connection failed", status_code=500)
        assert error.message == "Connection failed"
        assert error.status_code == 500

    def test_api_client_error_str(self):
        """Test error string representation."""
        error = ApiClientError("Network error")
        assert "Network error" in str(error)


class TestRecruitmentApiClient:
    """Tests for RecruitmentApiClient class."""

    @pytest.fixture
    def client(self):
        """Create API client instance."""
        return RecruitmentApiClient(base_url="http://localhost:8000")

    def test_client_initialization(self, client):
        """Test client is properly initialized."""
        assert client.base_url == "http://localhost:8000"
        assert client._session is not None

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_health_check_success(self, mock_client_class):
        """Test health check succeeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        result = client.health_check()
        
        assert result is True

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_health_check_failure(self, mock_client_class):
        """Test health check failure."""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        result = client.health_check()
        
        assert result is False

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_create_offer_success(self, mock_client_class):
        """Test successful offer creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "offer_id": "offer-123",
            "title": "Developer",
            "company": "TechCorp"
        }
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        input_data = OfferCreateInput(markdown_content="# Test Offer")
        result = client.create_offer(input_data)
        
        assert result is not None

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_get_offer_success(self, mock_client_class):
        """Test successful offer retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "offer_id": "offer-123",
            "title": "Senior Developer",
            "company": "TechCorp",
            "description": "Test",
            "keywords": ["python"],
            "created_at": "2025-04-05T10:00:00Z"
        }
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        result = client.get_offer("offer-123")
        
        assert result is not None

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_get_matching_success(self, mock_client_class):
        """Test successful matching retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "offer_id": "offer-123",
            "overall_confidence": 0.85,
            "experience_matches": [],
            "project_matches": [],
            "formation_matches": []
        }
        
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        result = client.get_matching("offer-123")
        
        assert result is not None

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_http_error_handling(self, mock_client_class):
        """Test HTTP error handling."""
        mock_session = Mock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_session.get.side_effect = HTTPStatusError("Not Found", request=Mock(), response=mock_response)
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        
        with pytest.raises(ApiClientError):
            client.get_offer("nonexistent")

    @patch("app.streamlit.services.api_client.httpx.Client")
    def test_connection_error_handling(self, mock_client_class):
        """Test connection error handling."""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection error")
        mock_client_class.return_value = mock_session
        
        client = RecruitmentApiClient(base_url="http://localhost:8000")
        
        with pytest.raises(ApiClientError):
            client.get_offer("test-id")

    def test_generation_workflow(self):
        """Test generation start and status retrieval workflow."""
        with patch("app.streamlit.services.api_client.httpx.Client") as mock_client_class:
            # Mock start generation
            start_response = Mock()
            start_response.status_code = 201
            start_response.json.return_value = {"generation_id": "gen-123"}
            
            # Mock status retrieval
            status_response = Mock()
            status_response.status_code = 200
            status_response.json.return_value = {
                "generation_id": "gen-123",
                "offer_id": "offer-123",
                "status": "completed"
            }
            
            mock_session = Mock()
            mock_session.post.return_value = start_response
            mock_session.get.return_value = status_response
            mock_client_class.return_value = mock_session
            
            client = RecruitmentApiClient(base_url="http://localhost:8000")
            gen_input = GenerationInput(offer_id="offer-123", language="en")
            
            # Start generation
            result = client.generate_cv_letter(gen_input)
            assert result is not None
            
            # Get status
            status = client.get_generation_status("gen-123")
            assert status is not None
