"""Business module for Streamlit tabs (OOP use cases)."""

from __future__ import annotations

import logging
from typing import Dict


from app.utils_functions import (
    GenerationInput,
    GenerationOutput,
    MatchingOutput,
    OfferCreateInput,
    OfferCreateOutput,
    OfferDetailsOutput,
)
from db_orchestration.config import OrchestrationConfig
from db_orchestration.ingest import OfferIngestionOrchestrator
from db_orchestration.database import Database
from db_orchestration.ingest import OfferSourceReader, OfferRecord, OfferRepositoryGateway
from pathlib import Path
import os


LOGGER = logging.getLogger(__name__)


class TabService:
    """Use-case layer consumed by UI pages (local orchestration version)."""

    def __init__(self, repo_root: Path | None = None) -> None:
        # Correction : toujours utiliser la racine du projet (dossier contenant src, db, etc.)
        if repo_root is None:
            # On part de ce fichier : src/app/domain/tab_service.py → .../src/app/domain → .../src → .../latex_tool_generator
            repo_root = Path(__file__).resolve().parents[3]
        self.repo_root = repo_root
        self.config = OrchestrationConfig.from_repo_root(self.repo_root)
        self.ingestor = OfferIngestionOrchestrator(self.config)
        self.db = Database(self.config.database_url)

    def submit_offer(self, offer_input: str, company: str, location: str, title: str) -> Dict[str, object]:
        # Ingestion locale, retourne un OfferCreateOutput minimal
        result = self.ingestor.run_from_payload(
            offer_input=offer_input,
            company=company,
            location=location,
            title=title,
            offer_path=None
        )
        return result

    def fetch_offer(self, offer_id: str) -> OfferDetailsOutput:
        # Lecture directe depuis la base locale
        row = self.db.fetch_one("SELECT * FROM offers WHERE offer_id = :offer_id", {"offer_id": offer_id})
        if not row:
            raise ValueError(f"Offer not found: {offer_id}")
        return OfferDetailsOutput(
            offer_id=row["offer_id"],
            offer_text=row["offer_text"],
            metadata_json=row["metadata_json"],
            keywords_json=row["keywords_json"],
            created_at=row["created_at"],
            company=row["company"],
            location=row["location"],
            title=row["title"]
        )

    def fetch_matching(self, offer_id: str, threshold: float) -> MatchingOutput:
        # Simule un matching local (à adapter selon logique réelle)
        # Ici, on retourne juste la structure attendue avec des valeurs factices
        return MatchingOutput(
            offer_id=offer_id,
            overall_confidence=1.0,
            experiences=[],
            projects=[],
            formations=[]
        )

    def start_generation(self, offer_id: str, language: str, force: bool) -> GenerationOutput:
        # Simule le démarrage d'une génération locale (à adapter selon logique réelle)
        return GenerationOutput(
            status="started",
            generation_id=f"gen-{offer_id}-{language}"
        )

    def read_generation_status(self, generation_id: str) -> GenerationOutput:
        # Simule le statut d'une génération locale (à adapter selon logique réelle)
        return GenerationOutput(
            status="completed",
            generation_id=generation_id
        )
