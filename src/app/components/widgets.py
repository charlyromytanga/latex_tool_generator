"""Blocs visuels réutilisables et helpers de feedback."""

from __future__ import annotations

import streamlit as st


def render_info_card(title: str, subtitle: str = "") -> None:
    """Affiche une carte d'information légère."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def render_json_block(data: object, label: str = "Payload") -> None:
    """Affiche un payload structuré de façon cohérente."""
    st.markdown(f"**{label}**")
    st.json(data)


def render_success(message: str) -> None:
    """Affiche un message de succès."""
    st.success(message)


def render_error(message: str) -> None:
    """Affiche un message d'erreur."""
    st.error(message)
