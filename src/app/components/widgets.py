from __future__ import annotations

import streamlit as st
import time
import os
import logging
from typing import Callable, Any, Dict, List, Optional
from app.services import ApiClientError
from app.domain.tab_service import TabService
from db_orchestration.ingest import OfferIngestionOrchestrator
from db_orchestration.config import OrchestrationConfig, LLMConfig
from db_orchestration.ingest import OfferSourceReader
from db_orchestration.database import Database, normalize_database_url
from pathlib import Path
from typing import Optional
import json


LOGGER = logging.getLogger(__name__)

# --- UploadOffer ---
def upload_offer_widget(service: TabService) -> None:
    with st.form("form_upload_offer", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        # Initialisation des champs (plus de reset manuel)
        if "upload_company" not in st.session_state:
            st.session_state.upload_company = ""
        if "upload_offer_title" not in st.session_state:
            st.session_state.upload_offer_title = ""
        if "upload_country" not in st.session_state:
            st.session_state.upload_country = "FR"
        if "upload_location" not in st.session_state:
            st.session_state.upload_location = ""
        if "upload_markdown" not in st.session_state:
            st.session_state.upload_markdown = ""
        if "result_offer" not in st.session_state:
            st.session_state.result_offer = {}
        with col1:
            company = st.text_input(
                label=" ",
                key="upload_company",
                placeholder="Company: Ex: Google, Amazon, BNP Paribas...",
                label_visibility="collapsed"
            )
        with col2:
            offer_title = st.text_input(
                label=" ",
                key="upload_offer_title",
                placeholder="Offer Title: Ex: Data Scientist, Consultant...",
                label_visibility="collapsed"
            )
        with col3:
            country = st.selectbox(
                label=" ",
                options=["FR", "EN", "LU", "CH"],
                key="upload_country",
                label_visibility="collapsed",
                placeholder="Country"
            )
        with col4:
            location = st.text_input(
                label=" ",
                key="upload_location",
                placeholder="Location: Ex: Paris, Lyon, Genève...",
                label_visibility="collapsed"
            )

        offer_input = st.text_area(
            "Offer Content",
            height=200,
            key="upload_markdown",
            placeholder="Paste the offer here and submit."
        )
        
        input_offer: List[str] = [company, offer_title, country, location, offer_input]
        submitted = st.form_submit_button("Submit", type="primary", key="btn_upload")

        if submitted:
            if not any(field.strip() for field in input_offer):
                render_error("Offer content is required.")
                return
            try:
                # Utilise le service (TabService) pour garantir la bonne config
                result_offer: Optional[Dict[str, object]] = service.submit_offer(
                    offer_input,
                    company,
                    location,
                    offer_title
                )
                st.toast("Offer ingested successfully!", icon="✅")
                with st.expander("Ingestion Result", expanded=False):
                    st.json(result_offer)
            except Exception as exc:
                LOGGER.exception("Offer ingestion error")
                render_error(f"Ingestion error: {exc}")


# --- AnalyzeOffer ---
def analyze_offer_widget(service: TabService) -> None:
    #render_info_card("Analyze Offer", "Load an offer by its ID.")
    default_offer_id: str = str(st.session_state.get("result_offer", {}).get("offer_id", "") or "")
    if "Id_offer" not in st.session_state:
        st.session_state.Id_offer = default_offer_id

    with st.form("form_analyze_offer", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])

        # Initialisation de l'état pour éviter KeyError
        if 'offer_details_keywords' not in st.session_state:
            st.session_state['offer_details_keywords'] = []

        with col1:
            offer_id = st.text_input(
                "Offer ID",
                value=st.session_state.Id_offer,
                key="analyze_offer_id",
                placeholder="Enter offer ID to analyze",
                label_visibility="collapsed"
            )
        with col2:
            submit_analyze = st.form_submit_button("Load Keywords", type="primary", key="btn_analyze")

        # Affichage de l'expander (Offer Details) seulement si non clear
        if submit_analyze:
            st.session_state['clear_offer_details'] = False
            try:
                extract_result = service.fetch_offer(offer_id.strip())
                st.session_state.Id_offer = extract_result.offer_id
                st.toast("Extracted successfully!", icon="✅")
                keywords = extract_result.keywords_json
                if isinstance(keywords, str):
                    try:
                        keywords_list = json.loads(keywords)
                    except Exception:
                        keywords_list = []
                elif isinstance(keywords, list):
                    keywords_list = keywords
                else:
                    keywords_list = []
                st.session_state['offer_details_keywords'] = keywords_list
            except ApiClientError as exc:
                LOGGER.exception("Analyze offer failed")
                render_error(str(exc))
                st.session_state['offer_details_keywords'] = []
        with col3:
            if st.session_state.Id_offer:
                st.markdown(
                    f'''
                    <input type="text" value="🆔 {st.session_state.Id_offer}" readonly
                        class="st-id-offer-input"
                        onclick="this.select();"
                    />
                    ''',
                    unsafe_allow_html=True,
                )
        keywords_list = st.session_state['offer_details_keywords']
        with st.expander("Offer Details", expanded=False):
            if isinstance(keywords_list, list):
                cols = st.columns(3)
                n = len(keywords_list)
                chunk = (n + 2) // 3
                for i, col in enumerate(cols):
                    with col:
                        for kw in keywords_list[i*chunk:(i+1)*chunk]:
                            st.markdown(f"- {kw}")
            else:
                st.write(f"type keywords: {type(keywords_list)}")







# --- MatchingPage ---
def matching_widget(service: TabService) -> None:
    render_info_card("Matching", "Visualize the matching of experiences/projects/education.")
    offer_id = st.session_state.get("Id_offer", "")
    threshold = st.slider("Threshold", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
    if st.button("Calculate / Read matching", key="btn_matching"):
        if not offer_id:
            render_error("No offer selected.")
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
    render_info_card("Generation CV + Lettre", "Start the generation for the current offer.")
    offer_id = st.session_state.get("Id_offer", "")
    language = st.selectbox("Language", options=["fr", "en"], index=0)
    force = st.checkbox("Force", value=False)
    if st.button("Generate", key="btn_generate"):
        if not offer_id:
            render_error("No offer selected.")
            return
        try:
            output = service.start_generation(offer_id=offer_id, language=language, force=force)
            st.session_state.generation_id = output.generation_id
            render_success(f"Generation started: {output.generation_id}")
            render_json_block(output.model_dump(), "Generation")
        except ApiClientError as exc:
            LOGGER.exception("Generation page failed")
            render_error(str(exc))

# --- PreviewPage ---
def preview_widget(service: TabService) -> None:
    render_info_card("Preview", "Display the current generation status.")
    generation_id: str = st.text_input(
        "Generation ID",
        value=str(st.session_state.get("generation_id") or ""),
        key="preview_generation_id",
    )
    if st.button("Check Status", key="btn_preview"):
        if not generation_id.strip():
            render_error("Generation ID required.")
            return
        try:
            output = service.read_generation_status(generation_id.strip())
            st.session_state.generation_id = output.generation_id
            render_json_block(output.model_dump(), "Status")
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
