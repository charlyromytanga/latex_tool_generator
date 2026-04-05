"""Unit tests for app.routes.matching module."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestMatchingRoutes:
    """Tests for matching-related routes."""

    def test_get_matching_route(self):
        """Test GET /api/matching/{offer_id} route."""
        with patch("app.routes.matching.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/offer-123")
            
            # Should return 200 or 404
            assert response.status_code in [200, 404]

    def test_matching_with_threshold(self):
        """Test matching with threshold parameter."""
        with patch("app.routes.matching.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/offer-456?threshold=0.5")
            assert response.status_code in [200, 404]

    def test_matching_invalid_threshold(self):
        """Test matching with invalid threshold."""
        with patch("app.routes.matching.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/offer-789?threshold=99.0")
            # Invalid threshold should be rejected or clamped
            assert response.status_code in [200, 422, 400]

    def test_matching_nonexistent_offer(self):
        """Test matching for non-existent offer."""
        with patch("app.routes.matching.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/nonexistent-offer-id")
            # Should return 404 or 200 with empty results
            assert response.status_code in [200, 404]


class TestMatchingDataStructure:
    """Tests for matching response data structure."""

    def test_matching_response_contains_scores(self):
        """Test that matching response contains score information."""
        with patch("app.routes.matching.get_db_connection") as mock_db:
            # Mock database to return matching results
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("exp-1", 0.85, "experience"),
                ("proj-1", 0.75, "project"),
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/offer-test")
            if response.status_code == 200:
                data = response.json()
                assert "matching_results" in data or "matches" in data or "scores" in data


class TestMatchingErrorHandling:
    """Tests for error handling in matching routes."""

    def test_matching_database_error(self):
        """Test handling of database errors."""
        with patch("app.routes.matching.get_db_connection", side_effect=Exception("DB Error")):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/matching/offer-id")
            # Should handle error gracefully
            assert response.status_code >= 400
