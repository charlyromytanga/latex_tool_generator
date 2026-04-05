"""Main OOP Streamlit application orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from app.streamlit.domain import TabService
from app.streamlit.pages import (
    AnalyzePage,
    GenerationPage,
    MatchingPage,
    PreviewPage,
    SettingsPage,
    UploadPage,
)
from app.streamlit.services import RecruitmentApiClient
from app.streamlit.utils_functions import AppSettings, SessionPayload


LOGGER = logging.getLogger(__name__)


class StreamlitApplication:
    """Composable Streamlit application with modular pages and services."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.api_client = RecruitmentApiClient(base_url=settings.api_base_url)
        self.tab_service = TabService(self.api_client)

    def run(self) -> None:
        st.set_page_config(page_title="Recruitment Assistant", layout="wide")
        self._init_session_state()
        self._apply_styles()
        self._render_sidebar()
        self._render_pages()

    def _init_session_state(self) -> None:
        payload = SessionPayload(
            offer_id=st.session_state.get("offer_id", ""),
            generation_id=st.session_state.get("generation_id", ""),
        )
        st.session_state.offer_id = payload.offer_id
        st.session_state.generation_id = payload.generation_id
        st.session_state.setdefault("theme", self.settings.theme)
        st.session_state.setdefault("default_language", self.settings.default_language)
        st.session_state.setdefault("threshold", self.settings.threshold)

    def _apply_styles(self) -> None:
        css_path = Path(__file__).resolve().parent / "assets" / "theme.css"
        try:
            css_content = css_path.read_text(encoding="utf-8")
            current_theme = st.session_state.get("theme", "light")
            css_override = ""
            if current_theme == "dark":
                css_override = """
                .stApp {
                    background: linear-gradient(160deg, #171f2a 0%, #12212c 45%, #17231f 100%);
                    color: #dbe7f3;
                }
                section[data-testid=\"stSidebar\"] {
                    background: linear-gradient(180deg, #1a2632 0%, #15202a 100%);
                    border-right: 1px solid #2a3a4a;
                }
                """
            st.markdown(f"<style>{css_content}\n{css_override}</style>", unsafe_allow_html=True)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unable to apply Streamlit CSS theme")

    def _render_sidebar(self) -> None:
        with st.sidebar:
            st.markdown("## Recruitment Assistant")
            st.caption("Design inspire de l'experience JobTeaser CY Tech")
            st.caption(f"API base URL: {self.settings.api_base_url}")
            try:
                health = self.api_client.health()
                st.success(f"API: {health.get('status', 'unknown')}")
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("API health check failed")
                st.warning("API indisponible")

    def _render_pages(self) -> None:
        upload_tab, analyze_tab, matching_tab, generation_tab, preview_tab, settings_tab = st.tabs(
            ["Upload Offre", "Analyse", "Matching", "Generation", "Preview", "Settings"]
        )

        pages = [
            (upload_tab, UploadPage(self.tab_service)),
            (analyze_tab, AnalyzePage(self.tab_service)),
            (matching_tab, MatchingPage(self.tab_service)),
            (generation_tab, GenerationPage(self.tab_service)),
            (preview_tab, PreviewPage(self.tab_service)),
            (settings_tab, SettingsPage(self.tab_service)),
        ]

        for tab, page in pages:
            with tab:
                try:
                    page.render()
                except Exception:  # pylint: disable=broad-except
                    LOGGER.exception("Unhandled page error: %s", page.name)
                    st.error(f"Erreur inattendue dans l'onglet: {page.name}")


def run_streamlit_app() -> None:
    """Entrypoint used by src/app/streamlit_app.py wrapper."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    settings = AppSettings()
    app = StreamlitApplication(settings=settings)
    app.run()
