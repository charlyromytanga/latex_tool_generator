"""
jobs_ingestor.py
----------------
Lit les fichiers sources depuis docs/offers/*.json
et peuple la table jobs via OfferRepositoryGateway.

Colonnes de la table jobs :
    id, language, country, city, company_name, company_type,
    offer_description, company_presentation, job_title
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from langdetect import detect

LOGGER = logging.getLogger(__name__)

# Chemin racine du dépôt (2 niveaux au-dessus de shared/)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCS_OFFERS = _REPO_ROOT / "docs" / "offers"
_DEFAULT_DB_PATH = _REPO_ROOT / "backend" / "db" / "jobcv.db"


# ---------------------------------------------------------------------------
# Dataclass miroir de la table jobs
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Lecteur de source JSON
# ---------------------------------------------------------------------------

class OfferSourceReader:
    """Load raw content from disk."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> Dict[str, Any]:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Offer file not found: {self.input_path}")
        return json.loads(self.input_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Gateway base de données
# ---------------------------------------------------------------------------

class OfferRepositoryGateway:
    """Database gateway for the `jobs` table."""

    def __init__(self, database: Any) -> None:
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


# ---------------------------------------------------------------------------
# Orchestrateur principal
# ---------------------------------------------------------------------------

class JobsIngestionOrchestrator:
    """
    Orchestre la lecture des JSON sources et l'insertion dans jobs via Database.

    Usage :
        config = OrchestrationConfig.from_repo_root(repo_root)
        orch = JobsIngestionOrchestrator(config)
        result = orch.run_from_file(Path("docs/offers/offer.json"))
        results = orch.run_all()
    """

    def __init__(self, config: Any | None = None) -> None:
        # Import local pour éviter la dépendance circulaire si utilisé hors du projet
        sys.path.insert(0, str(_REPO_ROOT))
        from shared.db_orchestration.config import OrchestrationConfig as OrchConfig  # type: ignore
        from shared.db_orchestration.database import Database  # type: ignore
        
        if config is None:
            config = OrchConfig.from_repo_root(_REPO_ROOT)
        
        self.config = config
        self.repo = OfferRepositoryGateway(Database(config.database_url))
    def _docs_offers_dir(self) -> Path:
        return self.config.sqlite_schema_path.resolve().parents[1] / "docs" / "offers"

    def _detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang if lang in ("fr", "en") else "fr"
        except Exception:
            return "fr"

    def _build_offer_document(
        self,
        record: JobRecord,
        offer_title: str | None = None,
    ) -> Dict[str, Any]:
        """Build a document dict to write as JSON."""
        reference = record.id.removeprefix("offer-") if record.id.startswith("offer-") else record.id
        return {
            "id": record.id,
            "reference": reference,
            "language": record.language,
            "country": record.country,
            "city": record.city,
            "company_name": record.company_name,
            "company_type": record.company_type,
            "offer_title": offer_title or record.job_title,
            "offer_description": record.offer_description,
            "company_presentation": record.company_presentation,
            "job_title": record.job_title,
        }

    def _write_offer_json(
        self,
        record: JobRecord,
        offer_title: str | None = None,
    ) -> Path:
        """Write offer as JSON to docs/offers/."""
        offers_dir = self._docs_offers_dir()
        offers_dir.mkdir(parents=True, exist_ok=True)
        json_path = offers_dir / f"{record.id}.json"
        json_payload = self._build_offer_document(record, offer_title=offer_title)
        json_path.write_text(
            json.dumps(json_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return json_path

    def run_from_file(self, offer_path: Path) -> Dict[str, Any]:
        """
        Ingère un seul fichier JSON source dans jobs.
        Si l'enregistrement existe déjà, il est supprimé puis réinséré.

        Returns:
            {"id": ..., "language": ..., "status": "inserted"|"replaced"} ou {"error": ...}
        """
        LOGGER.info("Ingestion offer ← %s", offer_path)
        try:
            raw = OfferSourceReader(offer_path).read()

            offer_id = raw.get("id") or f"offer-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
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

            # Detect if inserted or replaced
            exists = self.repo.database.fetch_one("SELECT id FROM jobs WHERE id = :id", {"id": offer_id})
            status = "replaced" if exists else "inserted"

            self.repo.upsert_job(record)
            self._write_offer_json(record, offer_title=offer_title)
            LOGGER.info("Offer %s → id=%s lang=%s", status, offer_id, language)
            return {"id": offer_id, "language": language, "status": status}
        except Exception as exc:
            LOGGER.exception("Erreur ingestion %s : %s", offer_path, exc)
            return {"file": str(offer_path), "error": str(exc)}

    def run_all(self, docs_dir: Path | None = None) -> List[Dict[str, Any]]:
        """
        Ingère tous les fichiers *.json présents dans docs_dir.

        Returns:
            Liste de résultats par fichier.
        """
        if docs_dir is None:
            docs_dir = self._docs_offers_dir()

        files = sorted(docs_dir.glob("*.json"))
        if not files:
            LOGGER.warning("Aucun fichier JSON trouvé dans %s", docs_dir)
            return []

        results = [self.run_from_file(f) for f in files]
        inserted = sum(1 for r in results if r.get("status") == "inserted")
        replaced = sum(1 for r in results if r.get("status") == "replaced")
        err = sum(1 for r in results if "error" in r)
        LOGGER.info(
            "offers ingestion terminée : %d inséré(s), %d remplacé(s), %d erreur(s)",
            inserted,
            replaced,
            err,
        )
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingestion offers depuis docs/offers/*.json")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        type=Path,
        help="Fichier JSON source (optionnel — si absent, ingère tous les fichiers de docs/offers/)",
    )
    parser.add_argument(
        "--db-path",
        default=str(_DEFAULT_DB_PATH),
        help=f"Chemin vers jobcv.db (défaut : {_DEFAULT_DB_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = _build_parser().parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    from shared.db_orchestration.config import OrchestrationConfig as OrchConfig  # type: ignore
    
    config = OrchConfig.from_repo_root(root)
    orch = JobsIngestionOrchestrator(config)

    if args.source:
        result = orch.run_from_file(args.source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if "error" not in result else 1
    else:
        results = orch.run_all()
        print(json.dumps(results, ensure_ascii=False, indent=2))
        errors = [r for r in results if "error" in r]
        return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
