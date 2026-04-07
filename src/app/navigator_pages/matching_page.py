"""Matching tab page."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.widgets import render_error, render_info_card, render_json_block
from app.navigator_pages.base_page import BasePage
from app.services import ApiClientError


LOGGER = logging.getLogger(__name__)


class MatchingPage(BasePage):
    """Display matching scores by threshold."""

    name = "Matching"

    def render(self) -> None:
        render_info_card("Matching", "Visualisez le matching experiences/projets/formations.")

        offer_id = st.session_state.get("offer_id", "")
        threshold = st.slider("Threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

        if st.button("Calculer / Lire matching", key="btn_matching"):
            if not offer_id:
                render_error("Aucune offre selectionnee.")
                return

            try:
                output = self.service.fetch_matching(offer_id=offer_id, threshold=threshold)
                st.metric("Overall confidence", output.overall_confidence)
                render_json_block(output.model_dump(), "Matching")
            except ApiClientError as exc:
                LOGGER.exception("Matching page failed")
                render_error(str(exc))
