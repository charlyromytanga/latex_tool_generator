"""Preview tab page."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.widgets import render_error, render_info_card, render_json_block
from app.pages.base_page import BasePage
from app.services import ApiClientError


LOGGER = logging.getLogger(__name__)


class PreviewPage(BasePage):
    """Display generation status as preview placeholder."""

    name = "Preview"

    def render(self) -> None:
        render_info_card("Preview", "Affiche le statut de generation courant.")

        generation_id: str = st.text_input(
            "Generation ID",
            value=str(st.session_state.get("generation_id") or ""),
            key="preview_generation_id",
        )

        if st.button("Verifier statut", key="btn_preview"):
            if not generation_id.strip():
                render_error("Generation ID requis.")
                return

            try:
                output = self.service.read_generation_status(generation_id.strip())
                st.session_state.generation_id = output.generation_id
                render_json_block(output.model_dump(), "Statut")
            except ApiClientError as exc:
                LOGGER.exception("Preview page failed")
                render_error(str(exc))
