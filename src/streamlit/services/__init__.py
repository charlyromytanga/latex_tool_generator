"""Service adapters for Streamlit UI."""

from .api_client import ApiClientError, RecruitmentApiClient

__all__ = ["RecruitmentApiClient", "ApiClientError"]
