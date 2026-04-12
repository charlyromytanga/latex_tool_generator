
"""Main OOP Streamlit application orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime
import streamlit as st
from pathlib import Path


from app.domain.tab_service import TabService
from app.components.widgets import (
    upload_offer_widget,
    analyze_offer_widget,
    matching_widget,
    generation_widget,
    preview_widget,
    settings_widget,
)
from app.services import RecruitmentApiClient
from app.utils_functions import AppSettings, SessionPayload


LOGGER = logging.getLogger(__name__)


class StreamlitApplication:
    """Composable Streamlit application with modular pages and services."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.tab_service = TabService()

    def run(self) -> None:
        st.set_page_config(page_title="Recruitment Assistant", layout="wide")
        self._init_session_state()
        self._apply_styles()
        self._render_pages()
        self._render_footer()

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
            # Forcer le thème clair partout (le reste du style est dans theme.css)
            css_override = """
            html, body, .stApp {
                background: #fff !important;
                color: var(--color-2, #1a2632) !important;
            }
            section[data-testid=\"stSidebar\"] {
                background: #fff !important;
                color: var(--color-2, #1a2632) !important;
                border-right: 1px solid #e0e0e0;
            }
            .stMarkdown, .stText, .stCaption, .stHeader, .stTitle, .stDataFrame, .stTable, .stTextInput, .stTextArea, .stButton, .stSelectbox, .stRadio, .stCheckbox, .stSlider, .stNumberInput, .stDateInput, .stTimeInput, .stColorPicker, .stFileUploader, .stForm, .stFormSubmitButton, .stMetric, .stTabs, .stTab, .stExpander, .stAlert, .stSuccess, .stWarning, .stError, .stInfo, .stCodeBlock, .stJson, .stImage, .stAudio, .stVideo, .stDownloadButton, .stProgress, .stSpinner, .stGraph, .stPlotlyChart, .stVegaLiteChart, .stDeckGlChart, .stBokehChart, .stPyDeckChart, .stAltairChart, .stMap, .stGraphvizChart, .stPlot, .stLatex, .stMarkdownContainer, .stMarkdownBlock, .stMarkdownText, .stMarkdownInline, .stMarkdownList, .stMarkdownTable, .stMarkdownCode, .stMarkdownMath, .stMarkdownLink, .stMarkdownImage, .stMarkdownHtml, .stMarkdownHr, .stMarkdownBlockquote, .stMarkdownHeading, .stMarkdownParagraph, .stMarkdownListItem, .stMarkdownTableCell, .stMarkdownTableRow, .stMarkdownTableHeader, .stMarkdownTableBody, .stMarkdownTableFooter, .stMarkdownTableCaption, .stMarkdownTableColgroup, .stMarkdownTableCol, .stMarkdownTableHead, .stMarkdownTableFoot, .stMarkdownTableRowGroup, .stMarkdownTableRowHeader, .stMarkdownTableRowBody, .stMarkdownTableRowFooter, .stMarkdownTableRowColgroup, .stMarkdownTableRowCol, .stMarkdownTableRowHead, .stMarkdownTableRowFoot, .stMarkdownTableRowBody, .stMarkdownTableRowHeader, .stMarkdownTableRowFooter, .stMarkdownTableRowColgroup, .stMarkdownTableRowCol, .stMarkdownTableRowHead, .stMarkdownTableRowFoot, .stMarkdownTableRowBody, .stMarkdownTableRowHeader, .stMarkdownTableRowFooter, .stMarkdownTableRowColgroup, .stMarkdownTableRowCol, .stMarkdownTableRowHead, .stMarkdownTableRowFoot, .stMarkdownTableRowBody, .stMarkdownTableRowHeader, .stMarkdownTableRowFooter {
                color: var(--color-2, #1a2632) !important;
            }
            """
            st.markdown(f"<style>{css_content}\n{css_override}</style>", unsafe_allow_html=True)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unable to apply Streamlit CSS theme")

    def _render_sidebar(self) -> None:
        # Désactivé : plus de sidebar
        pass

    def _render_pages(self) -> None:
        col_header_left, col_header_right = st.columns([3, 1])
        with col_header_left:
            st.markdown(
                """
                <h1 class="gradient-text">Recruitment Assistant</h1>
                <p>Candidate management and recruitment assistance.</p>
                """,
                unsafe_allow_html=True,
            )
        col_body_left, col_body_right = st.columns([2, 2])
        with col_body_left:
            st.markdown(
                """
                <div class="custom-bar-offre">
                    <span style="font-size:1.2em;vertical-align:middle;">📤</span>
                    <span>Import offer</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            upload_offer_widget(self.tab_service)

            st.markdown(
                """
                <div class="custom-bar-offre">
                    <span style="font-size:1.2em;vertical-align:middle;">🛠️</span>
                    <span>Data extractions</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            analyze_offer_widget(self.tab_service)


        with col_body_right:
            st.markdown(
                """
                <div class="offre-hero">
                    <h2>Gérez vos offres d'emploi efficacement</h2>
                    <p>Importez, analysez, générez des profils et suivez vos recrutements en un seul endroit.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            




    def _render_footer(self) -> None:

        st.markdown(
            f'''
            <footer class="custom-footer">
                <div class="footer-content">
                    <div class="footer-left"><strong>Recruitment Assistant</strong></div>
                    <div class="footer-center"><strong>AUTOMATICAL APPLIED PROCESS</strong></div>
                    <div class="footer-right">Charly-Romy Tanga | © {datetime.now().year}</div>
                </div>
            </footer>
            ''',
            unsafe_allow_html=True
        )


def run_streamlit_app() -> None:
    """Entrypoint used by src/app/streamlit_app.py wrapper."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    settings = AppSettings()
    app = StreamlitApplication(settings=settings)
    app.run()
