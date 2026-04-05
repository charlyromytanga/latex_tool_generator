"""Upload tab page."""

from __future__ import annotations

import logging

import streamlit as st

from app.streamlit.components import render_error, render_info_card, render_json_block, render_success
from streamlit.pages.base_page import BasePage
from streamlit.services import ApiClientError


LOGGER = logging.getLogger(__name__)


class UploadPage(BasePage):
    """Handle offer markdown submission."""

    name = "Upload Offre"

    def render(self) -> None:
        render_info_card("Upload Offre", "Collez le markdown de l'offre puis soumettez.")
        markdown_content = st.text_area("Markdown", height=260, key="upload_markdown")

        if st.button("Valider et Analyser", type="primary", key="btn_upload"):
            if not markdown_content.strip():
                render_error("Le markdown de l'offre est requis.")
                return

            try:
                output = self.service.submit_offer(markdown_content)
                st.session_state.offer_id = output.offer_id
                render_success(f"Offre creee: {output.offer_id}")
                render_json_block(output.model_dump(), "Resultat")
            except ApiClientError as exc:
                LOGGER.exception("Upload page failed")
                render_error(str(exc))
