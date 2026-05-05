"""Page objects for Streamlit tabs."""

from .analyze_page import AnalyzePage
from .generation_page import GenerationPage
from .matching_page import MatchingPage
from .preview_page import PreviewPage
from .settings_page import SettingsPage
from .upload_page import UploadPage

__all__ = [
    "UploadPage",
    "AnalyzePage",
    "MatchingPage",
    "GenerationPage",
    "PreviewPage",
    "SettingsPage",
]
