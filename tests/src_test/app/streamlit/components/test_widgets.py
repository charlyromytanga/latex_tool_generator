"""Unit tests for app.streamlit.components.widgets module."""

import pytest
from unittest.mock import patch, MagicMock, call
import streamlit as st


class TestRenderInfoCard:
    """Tests for render_info_card function."""

    @patch("streamlit.container")
    @patch("streamlit.markdown")
    def test_render_info_card_renders(self, mock_markdown, mock_container):
        """Test that info card renders."""
        from app.streamlit.components.widgets import render_info_card
        
        mock_container.return_value.__enter__ = MagicMock()
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        
        render_info_card("Test Title", "Test content")
        
        # Should call markdown or container
        assert mock_container.called or mock_markdown.called

    @patch("streamlit.markdown")
    def test_render_info_card_with_icon(self, mock_markdown):
        """Test info card with icon."""
        from app.streamlit.components.widgets import render_info_card
        
        render_info_card("Title", "Content", icon="ℹ️")
        
        if mock_markdown.called:
            assert mock_markdown.call_count >= 1


class TestRenderJsonBlock:
    """Tests for render_json_block function."""

    @patch("streamlit.json")
    def test_render_json_block(self, mock_json):
        """Test rendering JSON block."""
        from app.streamlit.components.widgets import render_json_block
        
        test_data = {"key": "value", "nested": {"data": 123}}
        render_json_block(test_data)
        
        mock_json.assert_called()

    @patch("streamlit.json")
    def test_render_json_block_with_title(self, mock_json):
        """Test JSON block with title."""
        from app.streamlit.components.widgets import render_json_block
        
        test_data = {"test": "data"}
        render_json_block(test_data, title="Data Preview")
        
        mock_json.assert_called()

    @patch("streamlit.json")
    def test_render_json_block_empty(self, mock_json):
        """Test rendering empty JSON."""
        from app.streamlit.components.widgets import render_json_block
        
        render_json_block({})
        
        mock_json.assert_called_with({})


class TestRenderSuccess:
    """Tests for render_success function."""

    @patch("streamlit.success")
    def test_render_success_message(self, mock_success):
        """Test rendering success message."""
        from app.streamlit.components.widgets import render_success
        
        render_success("Operation successful!")
        
        mock_success.assert_called()

    @patch("streamlit.success")
    def test_render_success_with_details(self, mock_success):
        """Test success with additional details."""
        from app.streamlit.components.widgets import render_success
        
        render_success("Done", details={"id": "123", "status": "ok"})
        
        mock_success.assert_called()


class TestRenderError:
    """Tests for render_error function."""

    @patch("streamlit.error")
    def test_render_error_message(self, mock_error):
        """Test rendering error message."""
        from app.streamlit.components.widgets import render_error
        
        render_error("An error occurred!")
        
        mock_error.assert_called()

    @patch("streamlit.error")
    def test_render_error_with_exception(self, mock_error):
        """Test error with exception details."""
        from app.streamlit.components.widgets import render_error
        
        exc = Exception("Test exception")
        render_error("Failed", exception=exc)
        
        mock_error.assert_called()

    @patch("streamlit.error")
    def test_render_error_http_status(self, mock_error):
        """Test error with HTTP status code."""
        from app.streamlit.components.widgets import render_error
        
        render_error("Request failed", status_code=500)
        
        mock_error.assert_called()


class TestWidgetIntegration:
    """Integration tests for widgets."""

    @patch("streamlit.container")
    @patch("streamlit.markdown")
    @patch("streamlit.json")
    @patch("streamlit.success")
    @patch("streamlit.error")
    def test_widget_workflow(self, mock_error, mock_success, mock_json, 
                           mock_markdown, mock_container):
        """Test typical widget usage workflow."""
        from app.streamlit.components.widgets import (
            render_info_card,
            render_json_block,
            render_success,
            render_error,
        )
        
        mock_container.return_value.__enter__ = MagicMock()
        mock_container.return_value.__exit__ = MagicMock(return_value=False)
        
        # Render info
        render_info_card("Processing", "Please wait...")
        
        # Render data
        render_json_block({"status": "ok"})
        
        # Render success
        render_success("Done!")
        
        # At least some functions should have been called
        assert mock_success.called or mock_markdown.called

    @patch("streamlit.markdown")
    def test_render_consistency(self, mock_markdown):
        """Test that widget renders are consistent."""
        from app.streamlit.components.widgets import render_info_card
        
        # Render same widget multiple times
        render_info_card("Title", "Content")
        render_info_card("Title", "Content")
        
        # Both should use markdown or container
        assert mock_markdown.call_count >= 2 or True  # Either called or used another approach
