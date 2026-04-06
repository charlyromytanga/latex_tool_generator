"""Settings page module (business-oriented tab)."""

from __future__ import annotations

import streamlit as st

from app.pages.base_page import BasePage


class SettingsPage(BasePage):
    """Manage UI/session settings used by all tabs."""

    name = "Settings"

    def render(self) -> None:
        st.subheader("Settings")

        theme = st.radio("Theme", options=["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
        st.session_state.theme = theme

        default_language = st.radio(
            "Langue par defaut",
            options=["fr", "en"],
            index=0 if st.session_state.default_language == "fr" else 1,
        )
        st.session_state.default_language = default_language

        threshold = st.slider(
            "Seuil matching par defaut",
            min_value=0.0,
            max_value=1.0,
            value=float(st.session_state.threshold),
            step=0.05,
        )
        st.session_state.threshold = threshold
