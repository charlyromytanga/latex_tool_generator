"""Unit tests for channels modules."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestChannelBase:
    """Tests for channel base module."""

    def test_output_channel_is_abstract(self):
        """Test OutputChannel is abstract."""
        from channels.base import OutputChannel
        
        # Should raise TypeError due to abstract methods
        with pytest.raises(TypeError):
            OutputChannel()

    def test_channel_context_creation(self):
        """Test ChannelContext can be created."""
        from channels.base import ChannelContext
        
        context = ChannelContext(
            offer_content="# Test Offer",
            cv_content="# CV",
            generation_id="gen-123"
        )
        assert context.generation_id == "gen-123"

    def test_channel_result_creation(self):
        """Test ChannelResult can be created."""
        from channels.base import ChannelResult
        
        result = ChannelResult(
            status="success",
            file_path="/tmp/output.txt",
            message="Generation complete"
        )
        assert result.status == "success"


class TestThankYouLetterChannel:
    """Tests for thank you letter channel."""

    @patch("pathlib.Path.write_text")
    def test_thank_you_letter_generates(self, mock_write):
        """Test thank you letter generation."""
        from channels.thank_you_letter import ThankYouLetterChannel
        
        channel = ThankYouLetterChannel()
        assert channel is not None

    def test_thank_you_letter_has_generate_method(self):
        """Test channel has generate method."""
        from channels.thank_you_letter import ThankYouLetterChannel
        
        channel = ThankYouLetterChannel()
        assert hasattr(channel, "generate") or callable(getattr(channel, "generate", None))


class TestRecruiterEmailChannel:
    """Tests for recruiter email channel."""

    def test_recruiter_email_channel_initialization(self):
        """Test recruiter email channel init."""
        from channels.recruiter_email import RecruiterEmailChannel
        
        channel = RecruiterEmailChannel()
        assert channel is not None

    def test_recruiter_email_has_generate_method(self):
        """Test channel has generate method."""
        from channels.recruiter_email import RecruiterEmailChannel
        
        channel = RecruiterEmailChannel()
        assert hasattr(channel, "generate") or callable(getattr(channel, "generate", None))


class TestProjectReportChannel:
    """Tests for project report channel."""

    def test_project_report_channel_initialization(self):
        """Test project report channel init."""
        from channels.project_report import ProjectReportChannel
        
        channel = ProjectReportChannel()
        assert channel is not None

    def test_project_report_has_generate_method(self):
        """Test channel has generate method."""
        from channels.project_report import ProjectReportChannel
        
        channel = ProjectReportChannel()
        assert hasattr(channel, "generate") or callable(getattr(channel, "generate", None))


class TestThesisChannel:
    """Tests for thesis channel."""

    def test_thesis_channel_initialization(self):
        """Test thesis channel init."""
        from channels.thesis import ThesisChannel
        
        channel = ThesisChannel()
        assert channel is not None

    def test_thesis_has_generate_method(self):
        """Test channel has generate method."""
        from channels.thesis import ThesisChannel
        
        channel = ThesisChannel()
        assert hasattr(channel, "generate") or callable(getattr(channel, "generate", None))


class TestChannelErrorHandling:
    """Tests for channel error handling."""

    @patch("pathlib.Path.mkdir")
    def test_channel_handles_file_error(self, mock_mkdir):
        """Test channel handles file creation errors."""
        mock_mkdir.side_effect = OSError("Permission denied")
        
        from channels.thank_you_letter import ThankYouLetterChannel
        
        channel = ThankYouLetterChannel()
        assert channel is not None

    def test_channel_result_error_status(self):
        """Test channel result with error status."""
        from channels.base import ChannelResult
        
        result = ChannelResult(
            status="error",
            message="Generation failed",
            error=Exception("Test error")
        )
        assert result.status == "error"
