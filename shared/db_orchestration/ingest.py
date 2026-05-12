"""
Offer ingestion orchestration :
Lecture d'une offre depuis un fichier JSON, extraction des champs principaux,
et insertion dans la base de données (table jobs — schéma actuel).

Colonnes de la table jobs :
  id, language, country, city, company_name, company_type,
  offer_description, company_presentation
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Sequence, Optional, Dict, List, Any
from uuid import uuid4
import unicodedata
import re
from langdetect import detect

from .config import OrchestrationConfig, LLMConfig
from .database import Database
import uuid

from dotenv import load_dotenv

load_dotenv()



LOGGER = logging.getLogger(__name__)



@dataclass(frozen=True)
class JobRecord:
    """Mirrors the `jobs` table schema exactly."""
    id: str
    language: str
    country: str
    city: Optional[str]
    company_name: Optional[str]
    company_type: Optional[str]
    offer_description: Optional[str]
    company_presentation: Optional[str]
    job_title: Optional[str]


class OfferSourceReader:
    """Load raw content from disk."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> str:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Offer file not found: {self.input_path}")
        return self.input_path.read_text(encoding="utf-8")


class OfferRepositoryGateway:
    """Database gateway for the `jobs` table."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def upsert_job(self, record: JobRecord) -> None:
        """Insert or replace a job offer into the `jobs` table."""
        sql = """
        INSERT OR REPLACE INTO jobs (
            id, language, country, city,
            company_name, company_type,
            offer_description, company_presentation, job_title
        ) VALUES (
            :id, :language, :country, :city,
            :company_name, :company_type,
            :offer_description, :company_presentation, :job_title
        )
        """
        self.database.execute(sql, asdict(record))


class OfferIngestionOrchestrator:

    def __init__(self, config: OrchestrationConfig) -> None:
        self.config = config
        self.repo = OfferRepositoryGateway(Database(config.database_url))

    def _detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang if lang in ("fr", "en") else "fr"
        except Exception:
            return "fr"

    def run_from_file(self, offer_path: Path) -> dict[str, Any]:
        """
        Lit un fichier JSON depuis docs/offers/ et insère l'offre dans la table `jobs`.
        Champs JSON supportés : id, language, country, city, company_name, company_type,
        offer_description, company_presentation, offer_title (ajouté en tête de offer_description).
        """
        raw = json.loads(offer_path.read_text(encoding="utf-8"))

        offer_id = raw.get("id") or f"offer-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

        description = raw.get("offer_description", "")
        offer_title = raw.get("offer_title", "")
        if offer_title and not description.startswith(offer_title):
            description = f"{offer_title}\n\n{description}"

        language = raw.get("language") or self._detect_language(description)
        country = raw.get("country", "").strip()
        if not country:
            raise ValueError(f"Champ 'country' manquant dans {offer_path}")

        record = JobRecord(
            id=offer_id,
            language=language,
            country=country,
            city=raw.get("city"),
            company_name=raw.get("company_name"),
            company_type=raw.get("company_type"),
            offer_description=description,
            company_presentation=raw.get("company_presentation"),
            job_title=raw.get("job_title"),
        )
        self.repo.upsert_job(record)
        LOGGER.info("Job ingested: id=%s company=%s country=%s", offer_id, record.company_name, record.country)

        return {
            "offer_id": offer_id,
            "company": record.company_name,
            "city": record.city,
            "country": record.country,
            "language": record.language,
        }

    def run_from_payload(
        self,
        offer_input: str,
        company: str,
        location: str,
        title: str,
        offer_path: Path | None = None,
        country: str = "France",
        city: str | None = None,
        company_type: str | None = None,
        company_presentation: str | None = None,
    ) -> dict[str, Any]:
        """Pipeline direct depuis des valeurs en mémoire — insère dans la table `jobs`."""
        offer_id = f"offer-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        language = self._detect_language(offer_input)
        description = f"{title}\n\n{offer_input}" if title else offer_input

        record = JobRecord(
            id=offer_id,
            language=language,
            country=country,
            city=city or location,
            company_name=company,
            company_type=company_type,
            offer_description=description,
            company_presentation=company_presentation,
            job_title=title,
        )
        self.repo.upsert_job(record)
        LOGGER.info("Job ingested: id=%s company=%s", offer_id, company)

        return {
            "offer_id": offer_id,
            "company": company,
            "city": record.city,
            "country": country,
            "language": language,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest one markdown offer into SQLite")
    parser.add_argument("offer_path", type=Path, help="Path to markdown offer file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    args = _build_parser().parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    config = OrchestrationConfig.from_repo_root(root)
    orchestrator = OfferIngestionOrchestrator(config)
    # Pour test CLI : lire le fichier comme texte brut et passer des valeurs factices pour company, location, title
    offer_input = args.offer_path.read_text(encoding="utf-8")
    company = "CLI_COMPANY"
    location = "CLI_LOCATION"
    title = "CLI_TITLE"
    result = orchestrator.run_from_payload(offer_input, company, location, title, args.offer_path)
    LOGGER.info("Ingestion result: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
