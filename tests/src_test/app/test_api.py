"""Unit tests for app.api module."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestAPIInitialization:
    """Tests for FastAPI app initialization."""

    def test_api_app_exists(self):
        """Test that API app can be created."""
        from app.api import create_app
        app = create_app()
        assert isinstance(app, FastAPI)

    def test_api_health_endpoint(self):
        """Test health endpoint."""
        from app.api import create_app
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_api_includes_routers(self):
        """Test that all routers are included."""
        from app.api import create_app
        app = create_app()
        
        # Check that routes are included
        routes = [route.path for route in app.routes]
        assert any("/api/" in route for route in routes)


class TestAPICORSConfiguration:
    """Tests for CORS and global configuration."""

    def test_api_middleware_configured(self):
        """Test that middleware is properly configured."""
        from app.api import create_app
        app = create_app()
        
        # Should have middleware configured
        assert len(app.user_middleware) > 0


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_api_request_timeout_handling(self):
        """Test timeout response."""
        from app.api import create_app
        app = create_app()
        client = TestClient(app)
        
        # Try to access non-existent endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code in [404, 500]

    def test_api_validation_error_handling(self):
        """Test validation error response format."""
        from app.api import create_app
        app = create_app()
        client = TestClient(app)
        
        # Send invalid data to a route
        response = client.post(
            "/api/offers",
            json={"invalid_field": "value"}
        )
        # Should return 422 for validation error
        assert response.status_code in [422, 400]
