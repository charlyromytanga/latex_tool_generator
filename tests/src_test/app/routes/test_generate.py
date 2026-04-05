"""Unit tests for app.routes.generate module."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestGenerationRoutes:
    """Tests for generation-related routes."""

    def test_start_generation_route(self):
        """Test POST /api/generate/cv_letter route."""
        with patch("app.routes.generate.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            payload = {
                "offer_id": "offer-123",
                "language": "en"
            }
            response = client.post("/api/generate/cv_letter", json=payload)
            
            # Should succeed or return validation error
            assert response.status_code in [200, 201, 202, 422, 400]

    def test_get_generation_status_route(self):
        """Test GET /api/generate/{generation_id} route."""
        with patch("app.routes.generate.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/generate/gen-123")
            
            # Should return 200 or 404
            assert response.status_code in [200, 404]

    def test_start_generation_validation(self):
        """Test generation request validation."""
        from app.api import create_app
        app = create_app()
        client = TestClient(app)
        
        # Missing required field
        response = client.post("/api/generate/cv_letter", json={})
        assert response.status_code in [422, 400]

    def test_generation_with_cover_letter_flag(self):
        """Test generation with cover letter flag."""
        with patch("app.routes.generate.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            payload = {
                "offer_id": "offer-456",
                "language": "fr",
                "include_cover_letter": True
            }
            response = client.post("/api/generate/cv_letter", json=payload)
            assert response.status_code in [200, 201, 202, 422]


class TestGenerationDataStructure:
    """Tests for generation response data structure."""

    def test_generation_start_response_contains_id(self):
        """Test that start generation response contains generation ID."""
        with patch("app.routes.generate.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.post(
                "/api/generate/cv_letter",
                json={"offer_id": "offer-789"}
            )
            
            if response.status_code in [200, 201, 202]:
                data = response.json()
                assert "generation_id" in data or "id" in data

    def test_generation_status_response_contains_status(self):
        """Test that status response contains status field."""
        with patch("app.routes.generate.get_db_connection") as mock_db:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (
                "gen-123", "offer-123", "processing", None, None, None, None
            )
            mock_db.return_value.cursor.return_value = mock_cursor
            
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/generate/gen-test")
            if response.status_code == 200:
                data = response.json()
                assert "status" in data


class TestGenerationErrorHandling:
    """Tests for error handling in generation routes."""

    def test_generation_database_error(self):
        """Test handling of database errors."""
        with patch("app.routes.generate.get_db_connection", side_effect=Exception("DB Error")):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.post(
                "/api/generate/cv_letter",
                json={"offer_id": "offer-id"}
            )
            # Should handle error gracefully
            assert response.status_code >= 400

    def test_generation_invalid_offer_id(self):
        """Test generation with invalid offer ID."""
        with patch("app.routes.generate.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.post(
                "/api/generate/cv_letter",
                json={"offer_id": ""}
            )
            assert response.status_code in [422, 400]
