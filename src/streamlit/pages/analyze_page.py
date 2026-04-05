"""Analyze tab page."""

from __future__ import annotations

import logging

import streamlit as st

from app.streamlit.components import render_error, render_info_card, render_json_block
from streamlit.pages.base_page import BasePage
from streamlit.services import ApiClientError


LOGGER = logging.getLogger(__name__)


class AnalyzePage(BasePage):
    """Display offer details and extracted keywords."""

    name = "Analyse"

    def render(self) -> None:
        render_info_card("Analyse Offre", "Charge une offre depuis son identifiant.")

        default_offer_id = st.session_state.get("offer_id", "")
        offer_id = st.text_input("Offer ID", value=default_offer_id, key="analyze_offer_id")

        if st.button("Charger l'offre", key="btn_analyze"):
            if not offer_id.strip():
                render_error("Offer ID requis.")
                return

            try:
                output = self.service.fetch_offer(offer_id.strip())
                st.session_state.offer_id = output.offer_id
                render_json_block(output.model_dump(), "Details offre")
            except ApiClientError as exc:
                LOGGER.exception("Analyze page failed")
                render_error(str(exc))
