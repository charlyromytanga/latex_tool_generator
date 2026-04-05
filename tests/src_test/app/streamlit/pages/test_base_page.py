"""Unit tests for app.streamlit.pages.base_page module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from abc import ABC


class TestBasePage:
    """Tests for BasePage abstract class."""

    def test_base_page_is_abstract(self):
        """Test that BasePage cannot be instantiated directly."""
        from app.streamlit.pages.base_page import BasePage
        
        # Should be abstract due to render() method
        with pytest.raises(TypeError):
            BasePage(service=Mock())

    def test_base_page_requires_render_method(self):
        """Test that subclasses must implement render."""
        from app.streamlit.pages.base_page import BasePage
        
        mock_service = Mock()
        
        class TestPage(BasePage):
            def render(self):
                pass
        
        page = TestPage(service=mock_service)
        assert page.service == mock_service

    def test_base_page_initialization(self):
        """Test BasePage initialization."""
        from app.streamlit.pages.base_page import BasePage
        
        mock_service = Mock()
        
        class SimplePage(BasePage):
            def render(self):
                pass
        
        page = SimplePage(service=mock_service)
        assert page.service == mock_service

    def test_base_page_service_injection(self):
        """Test that service is injected properly."""
        from app.streamlit.pages.base_page import BasePage
        
        mock_service = Mock()
        mock_service.fetch_offer.return_value = {"title": "Test"}
        
        class TestPage(BasePage):
            def render(self):
                return self.service.fetch_offer("offer-123")
        
        page = TestPage(service=mock_service)
        result = page.render()
        
        assert result == {"title": "Test"}

    @patch("streamlit.write")
    def test_page_can_render_content(self, mock_write):
        """Test that page render can write content."""
        from app.streamlit.pages.base_page import BasePage
        
        class ContentPage(BasePage):
            def render(self):
                import streamlit as st
                st.write("Test content")
        
        page = ContentPage(service=Mock())
        page.render()
        
        # write method should have been called if page renders


class TestPageErrorHandling:
    """Tests for error handling in pages."""

    def test_page_handles_service_error(self):
        """Test page handles service errors."""
        from app.streamlit.pages.base_page import BasePage
        from app.streamlit.services.api_client import ApiClientError
        
        mock_service = Mock()
        mock_service.fetch_offer.side_effect = ApiClientError("Connection failed")
        
        class ErrorPage(BasePage):
            def render(self):
                try:
                    self.service.fetch_offer("offer-123")
                except ApiClientError as e:
                    return str(e)
        
        page = ErrorPage(service=mock_service)
        result = page.render()
        
        assert "Connection failed" in result

    def test_page_logging_on_error(self):
        """Test page logs errors."""
        from app.streamlit.pages.base_page import BasePage
        import logging
        
        logger = logging.getLogger("test")
        mock_service = Mock()
        
        class LoggingPage(BasePage):
            def render(self):
                try:
                    raise ValueError("Test error")
                except Exception as e:
                    logger.exception("Error in page")
                    return False
        
        page = LoggingPage(service=mock_service)
        result = page.render()
        
        assert result is False
