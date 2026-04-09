"""Offer ingestion orchestration (Level 1).

Reads a markdown offer file, extracts normalized sections and stores it in `offers_raw`.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from .config import OrchestrationConfig
from .database import Database
from ..api._run.engine_keywords_extractor import extract_keywords
from ..api._run.engine_spacy_offer_extractor import extract_entities


LOGGER = logging.getLogger(__name__)



@dataclass(frozen=True)
class OfferRecord:
    offer_id: str
    offer_text: str
    metadata_json: str
    entities_json: str
    keywords_json: str
    created_at: str


class OfferSourceReader:
    """Load raw markdown content from disk."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> str:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Offer file not found: {self.input_path}")
        return self.input_path.read_text(encoding="utf-8")


class MarkdownOfferParser:
    """Parse markdown headings into canonical offer fields."""

    SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$")

    def parse(self, markdown_content: str) -> dict[str, object]:
        lines = markdown_content.splitlines()
        title = self._extract_title(lines)
        sections = self._extract_sections(lines)

        company_name = self._first_line(sections.get("entreprise", "")) or "Unknown Company"
        location = self._first_line(sections.get("localisation", "")) or "Unknown"
        tier_raw = self._first_line(sections.get("tier", "tier-2"))
        tier = self._normalize_tier(tier_raw)

        country = "Unknown"
        if "," in location:
            country = location.split(",")[-1].strip() or "Unknown"

        return {
            "title": title,
            "company": company_name,
            "location": location,
            "country": country,
            "tier": tier,
            "description": sections.get("description", "").strip(),
            "responsibilities": self._to_list(sections.get("responsabilites", "")),
            "skills": self._to_list(sections.get("competences requises", "")),
            "qualifications": self._to_list(sections.get("qualifications", "")),
            "benefits": self._to_list(sections.get("benefices", "")),
        }

    @staticmethod
    def _extract_title(lines: list[str]) -> str:
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.removeprefix("# ").strip()
        return "Untitled Offer"

    def _extract_sections(self, lines: list[str]) -> dict[str, str]:
        sections: dict[str, list[str]] = {}
        current_key = ""

        for line in lines:
            header_match = self.SECTION_PATTERN.match(line.strip())
            if header_match:
                current_key = header_match.group(1).strip().lower()
                sections[current_key] = []
                continue

            if current_key:
                sections[current_key].append(line)

        return {key: "\n".join(value).strip() for key, value in sections.items()}

    @staticmethod
    def _to_list(raw: str) -> list[str]:
        values: list[str] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                candidate = stripped.removeprefix("-").strip()
                if candidate:
                    values.append(candidate)
        return values

    @staticmethod
    def _first_line(raw: str) -> str:
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return ""

    @staticmethod
    def _normalize_tier(raw: str) -> str:
        normalized = raw.strip().lower()
        if normalized in {"tier-1", "tier-2", "tier-3"}:
            return normalized
        if normalized in {"tier 1", "1"}:
            return "tier-1"
        if normalized in {"tier 3", "3"}:
            return "tier-3"
        return "tier-2"



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
            entities_json,
            keywords_json,
            created_at
        ) VALUES (
            :offer_id,
            :offer_text,
            :metadata_json,
            :entities_json,
            :keywords_json,
            :created_at
        )
        """
        self.database.execute(sql, asdict(record))


class OfferIngestionOrchestrator:
    """Coordinates file read, parsing and persistence for a new offer."""

    def __init__(self, config: OrchestrationConfig) -> None:
        self.config = config
        # self.parser = MarkdownOfferParser()  # Désormais inutilisé
        self.repo = OfferRepositoryGateway(Database(config.database_url), config.schema_path)


    def run_from_file(self, offer_path: Path) -> dict[str, object]:
        from ..api._run.engine_spacy_offer_extractor import extract_entities
        from ..api._run.engine_keywords_extractor import extract_keywords
        import json
        import uuid
        reader = OfferSourceReader(offer_path)
        raw_text = reader.read()
        entities = extract_entities(raw_text, lang="fr")
        keywords = extract_keywords(raw_text, top_k=10)

        offer_id = f"offer-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        metadata = {
            "source_file": str(offer_path),
            "ingested_at": now
        }
        record = OfferRecord(
            offer_id=offer_id,
            offer_text=raw_text,
            metadata_json=json.dumps(metadata, ensure_ascii=True),
            entities_json=json.dumps(entities, ensure_ascii=True),
            keywords_json=json.dumps(keywords, ensure_ascii=True),
            created_at=now
        )
        self.repo.ensure_schema()
        self.repo.insert_offer(record)
        LOGGER.info("Offer ingested: offer_id=%s source=%s", offer_id, offer_path)
        return {
            "offer_id": offer_id,
            "offer_text": raw_text,
            "entities": entities,
            "keywords": keywords,
            "metadata": metadata,
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
    result = orchestrator.run_from_file(args.offer_path)
    LOGGER.info("Ingestion result: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
