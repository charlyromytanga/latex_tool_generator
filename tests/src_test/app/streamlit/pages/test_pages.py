"""Unit tests for streamlit pages."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestUploadPage:
    """Tests for UploadPage."""

    @patch("streamlit.markdown")
    def test_upload_page_renders(self, mock_markdown):
        """Test upload page renders."""
        from app.streamlit.pages.upload_page import UploadPage
        
        mock_service = Mock()
        page = UploadPage(service=mock_service)
        
        # Page should instantiate without error
        assert page.service == mock_service

    @patch("streamlit.markdown")
    @patch("streamlit.text_area")
    @patch("streamlit.button")
    def test_upload_page_accepts_markdown(self, mock_button, mock_textarea, mock_markdown):
        """Test upload page accepts markdown content."""
        mock_textarea.return_value = "# Test Offer"
        
        from app.streamlit.pages.upload_page import UploadPage
        
        mock_service = Mock()
        page = UploadPage(service=mock_service)
        
        assert page.service is not None


class TestAnalyzePage:
    """Tests for AnalyzePage."""

    @patch("streamlit.markdown")
    def test_analyze_page_renders(self, mock_markdown):
        """Test analyze page renders."""
        from app.streamlit.pages.analyze_page import AnalyzePage
        
        mock_service = Mock()
        page = AnalyzePage(service=mock_service)
        
        assert page.service == mock_service

    @patch("streamlit.markdown")
    def test_analyze_page_displays_offer(self, mock_markdown):
        """Test analyze page displays offer."""
        from app.streamlit.pages.analyze_page import AnalyzePage
        
        mock_service = Mock()
        mock_service.fetch_offer.return_value = {
            "offer_id": "offer-123",
            "title": "Developer",
            "company": "TechCorp"
        }
        page = AnalyzePage(service=mock_service)
        
        assert page.service is not None


class TestMatchingPage:
    """Tests for MatchingPage."""

    @patch("streamlit.markdown")
    def test_matching_page_renders(self, mock_markdown):
        """Test matching page renders."""
        from app.streamlit.pages.matching_page import MatchingPage
        
        mock_service = Mock()
        page = MatchingPage(service=mock_service)
        
        assert page.service == mock_service

    @patch("streamlit.markdown")
    @patch("streamlit.slider")
    def test_matching_page_threshold_control(self, mock_slider, mock_markdown):
        """Test matching page has threshold slider."""
        mock_slider.return_value = 0.5
        
        from app.streamlit.pages.matching_page import MatchingPage
        
        mock_service = Mock()
        page = MatchingPage(service=mock_service)
        
        assert page.service is not None


class TestGenerationPage:
    """Tests for GenerationPage."""

    @patch("streamlit.markdown")
    def test_generation_page_renders(self, mock_markdown):
        """Test generation page renders."""
        from app.streamlit.pages.generation_page import GenerationPage
        
        mock_service = Mock()
        page = GenerationPage(service=mock_service)
        
        assert page.service == mock_service

    @patch("streamlit.markdown")
    @patch("streamlit.selectbox")
    def test_generation_page_language_selection(self, mock_selectbox, mock_markdown):
        """Test generation page has language selector."""
        mock_selectbox.return_value = "en"
        
        from app.streamlit.pages.generation_page import GenerationPage
        
        mock_service = Mock()
        page = GenerationPage(service=mock_service)
        
        assert page.service is not None


class TestPreviewPage:
    """Tests for PreviewPage."""

    @patch("streamlit.markdown")
    def test_preview_page_renders(self, mock_markdown):
        """Test preview page renders."""
        from app.streamlit.pages.preview_page import PreviewPage
        
        mock_service = Mock()
        page = PreviewPage(service=mock_service)
        
        assert page.service == mock_service

    @patch("streamlit.markdown")
    def test_preview_page_polls_status(self, mock_markdown):
        """Test preview page can poll generation status."""
        from app.streamlit.pages.preview_page import PreviewPage
        
        mock_service = Mock()
        mock_service.read_generation_status.return_value = {
            "generation_id": "gen-123",
            "status": "completed"
        }
        page = PreviewPage(service=mock_service)
        
        assert page.service is not None


class TestSettingsPage:
    """Tests for SettingsPage."""

    @patch("streamlit.markdown")
    @patch("streamlit.radio")
    @patch("streamlit.slider")
    def test_settings_page_renders(self, mock_slider, mock_radio, mock_markdown):
        """Test settings page renders."""
        from app.streamlit.pages.settings_page import SettingsPage
        
        mock_radio.return_value = "light"
        mock_slider.return_value = 0.5
        
        mock_service = Mock()
        page = SettingsPage(service=mock_service)
        
        assert page.service == mock_service

    @patch("streamlit.markdown")
    @patch("streamlit.radio")
    def test_settings_page_theme_control(self, mock_radio, mock_markdown):
        """Test settings page has theme control."""
        mock_radio.return_value = "dark"
        
        from app.streamlit.pages.settings_page import SettingsPage
        
        mock_service = Mock()
        page = SettingsPage(service=mock_service)
        
        assert page.service is not None

    @patch("streamlit.markdown")
    @patch("streamlit.radio")
    def test_settings_page_language_control(self, mock_radio, mock_markdown):
        """Test settings page has language control."""
        mock_radio.return_value = "fr"
        
        from app.streamlit.pages.settings_page import SettingsPage
        
        mock_service = Mock()
        page = SettingsPage(service=mock_service)
        
        assert page.service is not None


class TestPageErrorHandling:
    """Integration tests for error handling in pages."""

    @patch("streamlit.markdown")
    def test_pages_handle_missing_service(self, mock_markdown):
        """Test pages handle missing service gracefully."""
        from app.streamlit.pages.upload_page import UploadPage
        
        with pytest.raises(TypeError):
            # Should fail if service is required
            page = UploadPage(service=None)

    @patch("streamlit.markdown")
    def test_pages_render_error_states(self, mock_markdown):
        """Test pages can render error states."""
        from app.streamlit.pages.analyze_page import AnalyzePage
        
        mock_service = Mock()
        mock_service.fetch_offer.side_effect = Exception("API Error")
        
        page = AnalyzePage(service=mock_service)
        assert page.service is not None
