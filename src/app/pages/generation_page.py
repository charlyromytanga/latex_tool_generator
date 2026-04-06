"""Generation tab page."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.widgets import render_error, render_info_card, render_json_block, render_success
from app.pages.base_page import BasePage
from app.services import ApiClientError


LOGGER = logging.getLogger(__name__)


class GenerationPage(BasePage):
    """Start generation and persist generation id in session."""

    name = "Generation"

    def render(self) -> None:
        render_info_card("Generation CV + Lettre", "Lance la generation pour l'offre courante.")

        offer_id = st.session_state.get("offer_id", "")
        language = st.selectbox("Langue", options=["fr", "en"], index=0)
        force = st.checkbox("Force", value=False)

        if st.button("Generer", key="btn_generate"):
            if not offer_id:
                render_error("Aucune offre selectionnee.")
                return

            try:
                output = self.service.start_generation(offer_id=offer_id, language=language, force=force)
                st.session_state.generation_id = output.generation_id
                render_success(f"Generation lancee: {output.generation_id}")
                render_json_block(output.model_dump(), "Generation")
            except ApiClientError as exc:
                LOGGER.exception("Generation page failed")
                render_error(str(exc))
