"""Reusable visual blocks and feedback helpers."""

from __future__ import annotations

import streamlit as st


def render_info_card(title: str, subtitle: str = "") -> None:
    """Render a lightweight information card."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def render_json_block(data: object, label: str = "Payload") -> None:
    """Render structured payload in a consistent way."""
    st.markdown(f"**{label}**")
    st.json(data)


def render_success(message: str) -> None:
    """Render success feedback."""
    st.success(message)


def render_error(message: str) -> None:
    """Render error feedback."""
    st.error(message)
