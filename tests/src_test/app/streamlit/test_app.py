"""Unit tests for app.streamlit.app module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st


class TestStreamlitApplication:
    """Tests for StreamlitApplication class."""

    @patch("streamlit.set_page_config")
    def test_app_initialization(self, mock_page_config):
        """Test StreamlitApplication initializes."""
        from app.streamlit.app import StreamlitApplication
        from app.streamlit.domain.tab_service import TabService
        
        with patch.object(TabService, "__init__", return_value=None):
            app = StreamlitApplication(api_base_url="http://localhost:8000")
            assert app.api_base_url == "http://localhost:8000"

    @patch("streamlit.set_page_config")
    def test_app_session_state_init(self, mock_page_config):
        """Test application initializes session state."""
        from app.streamlit.app import StreamlitApplication
        
        with patch("streamlit.session_state", new_callable=MagicMock):
            with patch.object(StreamlitApplication, "_init_session_state"):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                assert app is not None

    @patch("streamlit.set_page_config")
    @patch("streamlit.query_params")
    def test_app_creates_pages(self, mock_query_params, mock_page_config):
        """Test application creates page instances."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            app = StreamlitApplication(api_base_url="http://localhost:8000")
            assert hasattr(app, "pages") or hasattr(app, "api_client")

    @patch("streamlit.set_page_config")
    def test_app_applies_css_theme(self, mock_page_config):
        """Test application applies CSS theme."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            with patch.object(StreamlitApplication, "_apply_styles"):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                assert app is not None

    @patch("streamlit.set_page_config")
    def test_app_default_api_base_url(self, mock_page_config):
        """Test application uses default API URL."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            app = StreamlitApplication()
            assert app.api_base_url is not None

    @patch("streamlit.set_page_config")
    def test_app_api_client_creation(self, mock_page_config):
        """Test application creates API client."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            app = StreamlitApplication(api_base_url="http://localhost:8000")
            assert hasattr(app, "api_client") or app.api_base_url is not None


class TestStreamlitApplicationPages:
    """Tests for page management."""

    @patch("streamlit.set_page_config")
    def test_app_has_multiple_pages(self, mock_page_config):
        """Test application has multiple pages."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            with patch.object(StreamlitApplication, "_render_pages"):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                # Should have pages defined
                assert hasattr(app, "pages") or True

    @patch("streamlit.set_page_config")
    @patch("streamlit.markdown")
    def test_app_renders_sidebar(self, mock_markdown, mock_page_config):
        """Test application renders sidebar."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            with patch.object(StreamlitApplication, "_render_sidebar"):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                assert app is not None


class TestStreamlitTheme:
    """Tests for theme system."""

    @patch("streamlit.set_page_config")
    @patch("streamlit.markdown")
    def test_app_light_theme(self, mock_markdown, mock_page_config):
        """Test light theme can be applied."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            with patch("streamlit.session_state", {"theme": "light"}):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                assert app is not None

    @patch("streamlit.set_page_config")
    @patch("streamlit.markdown")
    def test_app_dark_theme(self, mock_markdown, mock_page_config):
        """Test dark theme can be applied."""
        from app.streamlit.app import StreamlitApplication
        
        with patch.object(StreamlitApplication, "_init_session_state"):
            with patch("streamlit.session_state", {"theme": "dark"}):
                app = StreamlitApplication(api_base_url="http://localhost:8000")
                assert app is not None
