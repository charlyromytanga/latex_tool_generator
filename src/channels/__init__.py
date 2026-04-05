"""Output channels for Level 3 document generation."""

from .base import ChannelContext, ChannelResult, OutputChannel
from .project_report import ProjectReportChannel
from .recruiter_email import RecruiterEmailChannel
from .thank_you_letter import ThankYouLetterChannel
from .thesis import ThesisChannel

__all__ = [
    "OutputChannel",
    "ChannelContext",
    "ChannelResult",
    "ThankYouLetterChannel",
    "RecruiterEmailChannel",
    "ProjectReportChannel",
    "ThesisChannel",
]
