from __future__ import annotations

import streamlit as st

import logging
from app.services import ApiClientError
from app.domain.tab_service import TabService


LOGGER = logging.getLogger(__name__)

# --- UploadPage ---
def upload_offer_widget(service: TabService) -> None:
    markdown_content = st.text_area(
        "Chargement de l'offre",
        height=500,
        key="upload_markdown",
        placeholder="Collez le markdown de l'offre puis soumettez."
    )
    if st.button("Valider et Analyser", type="primary", key="btn_upload"):
        if not markdown_content.strip():
            render_error("Le markdown de l'offre est requis.")
            return
        try:
            output = service.submit_offer(markdown_content)
            st.write("DEBUG output:", output)
            st.session_state.offer_id = getattr(output, "offer_id", "")
            render_success(f"Offre creee: {getattr(output, 'offer_id', 'Aucun ID')}")
            render_json_block(output.model_dump(), "Resultat")
        except ApiClientError as exc:
            LOGGER.exception("Upload page failed")
            render_error(f"Erreur API: {exc}")
        except Exception as exc:
            LOGGER.exception("Erreur inattendue upload")
            render_error(f"Erreur inattendue: {exc}")


# --- AnalyzePage ---
def analyze_offer_widget(service: TabService) -> None:
    render_info_card("Analyse Offre", "Charge une offre depuis son identifiant.")
    default_offer_id: str = str(st.session_state.get("offer_id") or "")
    offer_id: str = st.text_input("Offer ID", value=default_offer_id, key="analyze_offer_id")
    if st.button("Charger l'offre", key="btn_analyze"):
        if not offer_id.strip():
            render_error("Offer ID requis.")
            return
        try:
            output = service.fetch_offer(offer_id.strip())
            st.session_state.offer_id = output.offer_id
            render_json_block(output.model_dump(), "Details offre")
        except ApiClientError as exc:
            LOGGER.exception("Analyze page failed")
            render_error(str(exc))

# --- MatchingPage ---
def matching_widget(service: TabService) -> None:
    render_info_card("Matching", "Visualisez le matching experiences/projets/formations.")
    offer_id = st.session_state.get("offer_id", "")
    threshold = st.slider("Threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
    if st.button("Calculer / Lire matching", key="btn_matching"):
        if not offer_id:
            render_error("Aucune offre selectionnee.")
            return
        try:
            output = service.fetch_matching(offer_id=offer_id, threshold=threshold)
            st.metric("Overall confidence", output.overall_confidence)
            render_json_block(output.model_dump(), "Matching")
        except ApiClientError as exc:
            LOGGER.exception("Matching page failed")
            render_error(str(exc))

# --- GenerationPage ---
def generation_widget(service: TabService) -> None:
    render_info_card("Generation CV + Lettre", "Lance la generation pour l'offre courante.")
    offer_id = st.session_state.get("offer_id", "")
    language = st.selectbox("Langue", options=["fr", "en"], index=0)
    force = st.checkbox("Force", value=False)
    if st.button("Generer", key="btn_generate"):
        if not offer_id:
            render_error("Aucune offre selectionnee.")
            return
        try:
            output = service.start_generation(offer_id=offer_id, language=language, force=force)
            st.session_state.generation_id = output.generation_id
            render_success(f"Generation lancee: {output.generation_id}")
            render_json_block(output.model_dump(), "Generation")
        except ApiClientError as exc:
            LOGGER.exception("Generation page failed")
            render_error(str(exc))

# --- PreviewPage ---
def preview_widget(service: TabService) -> None:
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
            output = service.read_generation_status(generation_id.strip())
            st.session_state.generation_id = output.generation_id
            render_json_block(output.model_dump(), "Statut")
        except ApiClientError as exc:
            LOGGER.exception("Preview page failed")
            render_error(str(exc))

# --- SettingsPage ---
def settings_widget() -> None:
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
"""Blocs visuels réutilisables et helpers de feedback."""


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
