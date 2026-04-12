"""
Offer ingestion orchestration :
Lecture d'une offre depuis un fichier JSON, extraction des champs principaux (company, location, title),
extraction de mots-clés, et insertion dans la base de données (table offers).

Entités et extraction avancée désactivées (pipeline simplifié, extraction directe depuis le JSON).
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
import json
import uuid

from dotenv import load_dotenv

load_dotenv()



LOGGER = logging.getLogger(__name__)



@dataclass(frozen=True)
class OfferRecord:
    offer_id: Optional[str]
    offer_text: Optional[str]
    metadata_json: Optional[str]
    keywords_json: Optional[str]
    created_at: Optional[str]
    company: Optional[str]
    location: Optional[str]
    title: Optional[str]


class OfferSourceReader:
    """Load raw content from disk."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> str:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Offer file not found: {self.input_path}")
        return self.input_path.read_text(encoding="utf-8")




class OfferRepositoryGateway:
    """Database gateway for offers (nouvelle structure)."""

    def __init__(self, database: Database, schema_path: Path) -> None:
        self.database = database
        self.schema_path = schema_path.resolve()

    def ensure_schema(self) -> None:
        if self.database.has_table("offers"):
            return
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        self.database.execute_script(self.schema_path.read_text(encoding="utf-8"))

    def insert_offer(self, record: OfferRecord) -> None:
        sql = """
        INSERT INTO offers (
            offer_id,
            offer_text,
            metadata_json,
            keywords_json,
            created_at,
            company,
            location,
            title
        ) VALUES (
            :offer_id,
            :offer_text,
            :metadata_json,
            :keywords_json,
            :created_at,
            :company,
            :location,
            :title
        )
        """
        self.database.execute(sql, asdict(record))


class OfferIngestionOrchestrator:

    def __init__(self, config: OrchestrationConfig) -> None:
        """
        Orchestrateur d'ingestion d'offre :
        - Prend un fichier JSON d'offre en entrée
        - Extrait les champs principaux (company, location, title)
        - Extrait les mots-clés
        - Insère l'offre dans la base
        """
        self.config = config
        self.repo = OfferRepositoryGateway(Database(config.database_url), config.schema_path)

    def _detect_language(self, offer_input: str) -> str:
        """
        Détecte la langue du texte d'offre (français ou anglais, fallback fr).
        """
        try:
            lang = detect(offer_input)
            if lang not in ("fr", "en"):
                lang = "fr"
        except Exception:
            lang = "fr"
        return lang

    def extract_offer_text(self, raw) -> str:
        """
        Extrait le texte d'offre à partir du JSON (clé offer_input ou offer_text).
        """
        if isinstance(raw, dict):
            return raw.get("offer_input") or raw.get("offer_text") or ""
        return str(raw)

    def _normalize_keyword(self, kw: str) -> str:
        """
        Normalise un mot-clé (minuscule, sans accents, sans ponctuation).
        """
        kw = kw.lower().strip()
        kw = ''.join(c for c in unicodedata.normalize('NFD', kw) if unicodedata.category(c) != 'Mn')
        kw = re.sub(r"[\W_]+", " ", kw)
        kw = re.sub(r"\s+", " ", kw).strip()
        return kw

    def extract_company(self, raw, entities, description) -> Optional[str]:
        """
        Extrait le nom de l'entreprise depuis le JSON (clé company ou company_name).
        """
        if isinstance(raw, dict):
            company = raw.get("company") or raw.get("company_name")
            if company and str(company).strip():
                return company
        return None

    def extract_location(self, raw, entities, description) -> Optional[str]:
        """
        Extrait le lieu depuis le JSON (clé location).
        """
        if isinstance(raw, dict):
            location = raw.get("location")
            if location and str(location).strip():
                return location
        return None

    def extract_title(self, raw, entities, description) -> Optional[str]:
        """
        Extrait le titre depuis le JSON (clé offer_title ou title).
        """
        if isinstance(raw, dict):
            title = raw.get("offer_title") or raw.get("title")
            if title and str(title).strip():
                return title
        return None

    def run_from_payload(self, offer_input: str, company: str, location: str, title: str, offer_path: Path) -> dict[str, object]:
        """
        Pipeline principal : prend les champs du payload, extrait les mots-clés, et insère en base.
        """
        self.llm_config = LLMConfig(model_version="all-MiniLM-L6-v2")
        description = offer_input
        lang = self._detect_language(offer_input=description)
        keywords = self.llm_config.extract_keywords(description, top_k=100, stop_words=None if lang == "fr" else "english")
        preprocessed_keywords = [self._normalize_keyword(kw) for kw in keywords if isinstance(kw, str)]

        offer_id = f"offer-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat(timespec="seconds") + "Z"
        metadata = {
            "source_file": str(offer_path),
            "ingested_at": now,
            "lang": lang,
            "has_sections": False
        }

        # Robustesse : lever une erreur explicite si un champ clé est manquant ou vide
        missing = []
        if not company or not str(company).strip():
            missing.append("company")
        if not location or not str(location).strip():
            missing.append("location")
        if not title or not str(title).strip():
            missing.append("title")
        if missing:
            raise ValueError(f"Champ(s) obligatoire(s) manquant(s) ou vide(s) dans l'offre : {', '.join(missing)}")

        record = OfferRecord(
            offer_id=offer_id,
            offer_text=description,
            metadata_json=json.dumps(metadata, ensure_ascii=True),
            keywords_json=json.dumps(preprocessed_keywords, ensure_ascii=True),
            created_at=now,
            company=company,
            location=location,
            title=title
        )
        self.repo.ensure_schema()
        self.repo.insert_offer(record)
        LOGGER.info("Offer ingested: offer_id=%s source=%s lang=%s", offer_id, offer_path, lang)

        return {
            "offer_id": offer_id,
            "company": company,
            "location": location,
            "title": title,
            "keywords": preprocessed_keywords,
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
