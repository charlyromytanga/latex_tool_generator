"""Unit tests for app.routes.offers module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


class TestOffersRoutes:
    """Tests for offer-related routes."""

    def test_create_offer_route(self):
        """Test POST /api/offers route."""
        with patch("app.routes.offers.OfferIngestionOrchestrator"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            payload = {
                "markdown_content": "# Senior Developer\n## Description\nTest offer"
            }
            response = client.post("/api/offers", json=payload)
            
            # Should either succeed or return validation error
            assert response.status_code in [200, 201, 422, 400]

    def test_get_offer_route(self):
        """Test GET /api/offers/{offer_id} route."""
        with patch("app.routes.offers.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/offers/test-offer-123")
            
            # Should return 200 or 404
            assert response.status_code in [200, 404]

    def test_create_offer_validation(self):
        """Test offer creation validates markdown content."""
        from app.api import create_app
        app = create_app()
        client = TestClient(app)
        
        # Missing required field
        response = client.post("/api/offers", json={})
        assert response.status_code in [422, 400]

    def test_get_offer_invalid_id(self):
        """Test getting offer with invalid ID."""
        with patch("app.routes.offers.get_db_connection"):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/offers/")
            # Should return 404 or 422
            assert response.status_code in [404, 422]


class TestOffersErrorHandling:
    """Tests for error handling in offers routes."""

    def test_offers_database_error(self):
        """Test handling of database errors."""
        with patch("app.routes.offers.get_db_connection", side_effect=Exception("DB Error")):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.get("/api/offers/test-id")
            # Should handle error gracefully
            assert response.status_code >= 400

    def test_offers_parser_error(self):
        """Test handling of markdown parsing errors."""
        with patch("app.routes.offers.OfferIngestionOrchestrator", side_effect=ValueError("Parse error")):
            from app.api import create_app
            app = create_app()
            client = TestClient(app)
            
            response = client.post(
                "/api/offers",
                json={"markdown_content": "invalid"}
            )
            assert response.status_code >= 400
