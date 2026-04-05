"""Base page abstraction for OOP Streamlit tabs."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.streamlit.domain import TabService


class BasePage(ABC):
    """Common contract for each Streamlit tab page."""

    name: str

    def __init__(self, service: TabService) -> None:
        self.service = service

    @abstractmethod
    def render(self) -> None:
        """Render page content."""
