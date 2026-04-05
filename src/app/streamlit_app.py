"""Minimal Streamlit UI scaffold aligned with APP_STREAMLIT specification."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
import streamlit as st


API_BASE_URL = os.getenv("RECRUITMENT_API_BASE_URL", "http://localhost:8000")


def _api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    with httpx.Client(timeout=15.0) as client:
        response = client.get(f"{API_BASE_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()


def _api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{API_BASE_URL}{path}", json=payload)
        response.raise_for_status()
        return response.json()


def _init_state() -> None:
    st.session_state.setdefault("offer_id", "")
    st.session_state.setdefault("generation_id", "")


def main() -> None:
    st.set_page_config(page_title="Recruitment Assistant", layout="wide")
    _init_state()

    st.title("Recruitment Assistant V2")
    st.caption("UI scaffold for offer ingestion, matching and generation.")

    with st.sidebar:
        st.header("Settings")
        st.text_input("API Base URL", value=API_BASE_URL, disabled=True)

    upload_tab, analyze_tab, matching_tab, generate_tab, preview_tab = st.tabs(
        ["Upload Offre", "Analyse", "Matching", "Generation", "Preview"]
    )

    with upload_tab:
        st.subheader("Upload Offre")
        markdown_content = st.text_area("Markdown de l'offre", height=300)
        if st.button("Valider et Analyser", type="primary"):
            if not markdown_content.strip():
                st.warning("Le markdown de l'offre est requis.")
            else:
                result = _api_post(
                    "/api/offers",
                    {"markdown_content": markdown_content, "source_file": "streamlit_input.md"},
                )
                st.session_state.offer_id = result["offer_id"]
                st.success(f"Offre creee: {result['offer_id']}")
                st.json(result)

    with analyze_tab:
        st.subheader("Analyse Offre")
        offer_id = st.text_input("Offer ID", value=st.session_state.offer_id)
        if st.button("Charger l'offre") and offer_id.strip():
            result = _api_get(f"/api/offers/{offer_id.strip()}")
            st.json(result)
            st.session_state.offer_id = offer_id.strip()

    with matching_tab:
        st.subheader("Matching")
        threshold = st.slider("Threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
        if st.button("Calculer / Lire matching") and st.session_state.offer_id:
            result = _api_get(
                f"/api/matching/{st.session_state.offer_id}",
                params={"threshold": threshold, "limit": 10},
            )
            st.metric("Overall confidence", result.get("overall_confidence", 0.0))
            st.json(result)

    with generate_tab:
        st.subheader("Generation CV + Lettre")
        language = st.selectbox("Langue", options=["fr", "en"], index=0)
        force = st.checkbox("Force", value=False)
        if st.button("Generer"):
            if not st.session_state.offer_id:
                st.warning("Aucune offre selectionnee.")
            else:
                result = _api_post(
                    "/api/generate/cv_letter",
                    {
                        "offer_id": st.session_state.offer_id,
                        "language": language,
                        "force": force,
                    },
                )
                st.session_state.generation_id = result["generation_id"]
                st.success(f"Generation lancee: {result['generation_id']}")
                st.json(result)

    with preview_tab:
        st.subheader("Preview (statut generation)")
        generation_id = st.text_input("Generation ID", value=st.session_state.generation_id)
        if st.button("Verifier statut") and generation_id.strip():
            result = _api_get(f"/api/generate/{generation_id.strip()}")
            st.code(json.dumps(result, indent=2, ensure_ascii=True), language="json")


if __name__ == "__main__":
    main()
