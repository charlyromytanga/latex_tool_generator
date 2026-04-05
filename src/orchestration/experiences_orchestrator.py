"""my_experiences bootstrap orchestration.

Pipeline (4 layers):
1) Ingestion: read standardized JSON/Markdown from data/experiences.
2) Normalization: sanitize and map source payload to DB-ready records.
3) Validation: enforce minimal required fields.
4) Persistence: upsert validated records into SQLite my_experiences.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid5, NAMESPACE_URL


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExperienceRecord:
    """Canonical normalized record for my_experiences."""

    exp_id: str
    company: str
    role: str
    duration_months: int | None
    description: str
    skills: list[str]
    achievements: list[str]
    start_date: str | None
    end_date: str | None
    tags: list[str]


class ExperienceSourceReader:
    """Reads experience payload from a standardized local input file."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> list[dict[str, Any]]:
        """Read source payload and return raw experience items."""
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        suffix = self.input_path.suffix.lower()
        if suffix == ".json":
            return self._read_json()
        if suffix == ".md":
            return self._read_markdown()

        raise ValueError(f"Unsupported input format: {self.input_path.suffix}")

    def _read_json(self) -> list[dict[str, Any]]:
        content = json.loads(self.input_path.read_text(encoding="utf-8"))
        if isinstance(content, list):
            return [item for item in content if isinstance(item, dict)]
        if isinstance(content, dict):
            items = content.get("experiences", [])
            if not isinstance(items, list):
                raise ValueError("JSON field 'experiences' must be a list")
            return [item for item in items if isinstance(item, dict)]
        raise ValueError("JSON root must be an object or list")

    def _read_markdown(self) -> list[dict[str, Any]]:
        # Minimal markdown fallback parser for sectioned input.
        lines = self.input_path.read_text(encoding="utf-8").splitlines()
        records: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        for line in lines:
            value = line.strip()
            if value.startswith("### "):
                if current:
                    records.append(current)
                current = {
                    "role": value.removeprefix("### ").strip(),
                    "skills": [],
                    "achievements": [],
                    "tags": [],
                }
                continue

            if current is None:
                continue

            if value.startswith("- Company:"):
                current["company"] = value.split(":", 1)[1].strip()
            elif value.startswith("- Dates:"):
                raw = value.split(":", 1)[1].strip()
                if " to " in raw:
                    start_s, end_s = [part.strip() for part in raw.split(" to ", 1)]
                    current["start_date"] = start_s
                    current["end_date"] = None if end_s.lower() == "present" else end_s
            elif value.startswith("- Skills:"):
                skills_str = value.split(":", 1)[1].strip()
                current["skills"] = [s.strip() for s in skills_str.split(",") if s.strip()]
            elif value.startswith("- Key points:"):
                continue
            elif value.startswith("-"):
                point = value.removeprefix("-").strip()
                if point:
                    current.setdefault("achievements", []).append(point)

        if current:
            records.append(current)

        return records


class ExperienceNormalizer:
    """Maps source dictionaries into ExperienceRecord structures."""

    @staticmethod
    def normalize_many(items: list[dict[str, Any]]) -> list[ExperienceRecord]:
        records: list[ExperienceRecord] = []
        for item in items:
            normalized = ExperienceNormalizer.normalize_one(item)
            if normalized is not None:
                records.append(normalized)
        return records

    @staticmethod
    def normalize_one(item: dict[str, Any]) -> ExperienceRecord | None:
        company = _clean_text(item.get("company"))
        role = _clean_text(item.get("role"))
        description = _clean_text(item.get("description"))

        if not description:
            achievements_fallback = _to_str_list(item.get("achievements"))
            if achievements_fallback:
                description = achievements_fallback[0]

        if not company or not role or not description:
            LOGGER.warning(
                "Skipping invalid experience (missing company/role/description): %s",
                item,
            )
            return None

        start_date = _normalize_date(item.get("start_date"))
        end_date = _normalize_date(item.get("end_date"))

        exp_id = _clean_text(item.get("experience_id")) or _stable_experience_id(
            company=company,
            role=role,
            start_date=start_date,
        )

        skills = _to_str_list(item.get("skills"))
        achievements = _to_str_list(item.get("achievements"))
        tags = _to_str_list(item.get("tags"))
        duration = _compute_duration_months(start_date, end_date)

        return ExperienceRecord(
            exp_id=exp_id,
            company=company,
            role=role,
            duration_months=duration,
            description=description,
            skills=skills,
            achievements=achievements,
            start_date=start_date,
            end_date=end_date,
            tags=tags,
        )


class ExperienceRepositoryGateway:
    """DB gateway for my_experiences writes."""

    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = db_path.resolve()
        self.schema_path = schema_path.resolve()

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='my_experiences'"
            ).fetchone()
            if table_exists:
                return

            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

            LOGGER.info("my_experiences missing, initializing schema from %s", self.schema_path)
            conn.executescript(self.schema_path.read_text(encoding="utf-8"))
            conn.commit()

    def upsert_many(self, records: list[ExperienceRecord]) -> tuple[int, int]:
        sql = """
        INSERT INTO my_experiences (
            exp_id,
            company,
            role,
            duration_months,
            description,
            skills_json,
            achievements_json,
            start_date,
            end_date,
            tags_json
        ) VALUES (
            :exp_id,
            :company,
            :role,
            :duration_months,
            :description,
            :skills_json,
            :achievements_json,
            :start_date,
            :end_date,
            :tags_json
        )
        ON CONFLICT(exp_id) DO UPDATE SET
            company = excluded.company,
            role = excluded.role,
            duration_months = excluded.duration_months,
            description = excluded.description,
            skills_json = excluded.skills_json,
            achievements_json = excluded.achievements_json,
            start_date = excluded.start_date,
            end_date = excluded.end_date,
            tags_json = excluded.tags_json,
            indexed_at = CURRENT_TIMESTAMP
        """

        inserted = 0
        updated = 0

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            for record in records:
                existed = conn.execute(
                    "SELECT 1 FROM my_experiences WHERE exp_id = ?",
                    (record.exp_id,),
                ).fetchone()

                payload = {
                    "exp_id": record.exp_id,
                    "company": record.company,
                    "role": record.role,
                    "duration_months": record.duration_months,
                    "description": record.description,
                    "skills_json": json.dumps(record.skills, ensure_ascii=True),
                    "achievements_json": json.dumps(record.achievements, ensure_ascii=True),
                    "start_date": record.start_date,
                    "end_date": record.end_date,
                    "tags_json": json.dumps(record.tags, ensure_ascii=True),
                }
                conn.execute(sql, payload)

                if existed:
                    updated += 1
                else:
                    inserted += 1

            conn.commit()

        return inserted, updated


class ExperiencesBootstrapOrchestrator:
    """Orchestrates ingestion from data/experiences into my_experiences."""

    def __init__(
        self,
        input_path: Path,
        db_path: Path,
        schema_path: Path,
        dry_run: bool = False,
    ) -> None:
        self.input_path = input_path.resolve()
        self.dry_run = dry_run
        self.reader = ExperienceSourceReader(self.input_path)
        self.gateway = ExperienceRepositoryGateway(db_path=db_path, schema_path=schema_path)

    def run(self) -> None:
        LOGGER.info("Starting my_experiences bootstrap from %s", self.input_path)

        raw_items = self.reader.read()
        LOGGER.info("Ingestion layer: %d raw records loaded", len(raw_items))

        records = ExperienceNormalizer.normalize_many(raw_items)
        LOGGER.info("Normalization/validation layer: %d valid records", len(records))

        if self.dry_run:
            LOGGER.info("Dry-run mode enabled: no database write performed")
            for rec in records:
                LOGGER.debug("DRY-RUN record=%s company=%s role=%s", rec.exp_id, rec.company, rec.role)
            return

        self.gateway.ensure_schema()
        inserted, updated = self.gateway.upsert_many(records)
        LOGGER.info(
            "Persistence layer complete: inserted=%d updated=%d total=%d",
            inserted,
            updated,
            len(records),
        )


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result = [str(item).strip() for item in value if str(item).strip()]
        return sorted(set(result))
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return sorted(set(parts))
    return []


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    date_str = str(value).strip()
    if not date_str:
        return None

    patterns = ("%Y-%m-%d", "%Y-%m", "%Y")
    for pattern in patterns:
        try:
            parsed = datetime.strptime(date_str, pattern)
            if pattern == "%Y":
                return f"{parsed.year:04d}-01-01"
            if pattern == "%Y-%m":
                return f"{parsed.year:04d}-{parsed.month:02d}-01"
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _stable_experience_id(company: str, role: str, start_date: str | None) -> str:
    seed = f"{company.lower()}|{role.lower()}|{start_date or 'unknown'}"
    return str(uuid5(NAMESPACE_URL, seed))


def _compute_duration_months(start_date: str | None, end_date: str | None) -> int | None:
    if not start_date:
        return None

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    if end_date is None:
        end = date.today()
    else:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return None

    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day >= start.day:
        months += 1
    return max(months, 0)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap my_experiences from standardized local JSON/Markdown input."
    )
    parser.add_argument(
        "--input-path",
        default="data/experiences/linkedin_charly_romy_tanga.json",
        help="Input file (.json or .md) containing standardized experiences",
    )
    parser.add_argument(
        "--db-path",
        default="db/recruitment_assistant.db",
        help="SQLite database path",
    )
    parser.add_argument(
        "--schema-path",
        default="db/schema_init.sql",
        help="Schema file used to initialize DB when needed",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run ingestion/normalization/validation without writing to DB",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    orchestrator = ExperiencesBootstrapOrchestrator(
        input_path=Path(args.input_path),
        db_path=Path(args.db_path),
        schema_path=Path(args.schema_path),
        dry_run=args.dry_run,
    )

    try:
        orchestrator.run()
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("my_experiences bootstrap failed")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
