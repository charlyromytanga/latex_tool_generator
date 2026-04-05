"""formations orchestration.

Pipeline (4 layers):
1) Ingestion: read standardized JSON/Markdown from data/formations.
2) Normalization: sanitize and map source payload to canonical records.
3) Persistence: upsert validated records into SQLite formations.
4) Output: generate the LaTeX formation section for future CV templates.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from uuid import NAMESPACE_URL, uuid5


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FormationRecord:
    """Canonical formation payload used for DB writes and LaTeX rendering."""

    formation_id: str
    institution: str
    program: str
    degree: str
    location: str
    start_date: str | None
    end_date: str | None
    is_current: bool
    description: str
    courses: list[str]
    course_categories: dict[str, list[str]]
    achievements: list[str]
    tags: list[str]


class FormationSourceReader:
    """Reads formations from a standardized local file."""

    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path.resolve()

    def read(self) -> list[dict[str, Any]]:
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        suffix = self.input_path.suffix.lower()
        if suffix == ".json":
            payload = json.loads(self.input_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                items = payload.get("formations", [])
                if not isinstance(items, list):
                    raise ValueError("JSON field 'formations' must be a list")
                return [item for item in items if isinstance(item, dict)]
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
            raise ValueError("JSON root must be object or list")

        if suffix == ".md":
            return self._read_markdown()

        raise ValueError(f"Unsupported file format: {self.input_path.suffix}")

    def _read_markdown(self) -> list[dict[str, Any]]:
        lines = self.input_path.read_text(encoding="utf-8").splitlines()
        records: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        for line in lines:
            value = line.strip()
            if value.startswith("### "):
                if current:
                    records.append(current)
                current = {
                    "institution": value.removeprefix("### ").strip(),
                    "achievements": [],
                }
                continue

            if current is None or not value.startswith("-"):
                continue

            if value.startswith("- Program:"):
                current["program"] = value.split(":", 1)[1].strip()
            elif value.startswith("- Degree:"):
                current["degree"] = value.split(":", 1)[1].strip()
            elif value.startswith("- Location:"):
                current["location"] = value.split(":", 1)[1].strip()
            elif value.startswith("- Dates:"):
                raw = value.split(":", 1)[1].strip()
                if " to " in raw:
                    start_s, end_s = [part.strip() for part in raw.split(" to ", 1)]
                    current["start_date"] = _normalize_date(start_s)
                    current["end_date"] = None if end_s.lower() == "present" else _normalize_date(end_s)
                else:
                    current["start_date"] = None
                    current["end_date"] = None
            elif value.startswith("- Description:"):
                continue
            else:
                point = value.removeprefix("-").strip()
                if point:
                    current.setdefault("achievements", []).append(point)

        if current:
            records.append(current)

        return records


class FormationNormalizer:
    """Normalize and validate raw formation dictionaries."""

    @staticmethod
    def normalize_many(items: list[dict[str, Any]]) -> list[FormationRecord]:
        records: list[FormationRecord] = []
        for item in items:
            rec = FormationNormalizer.normalize_one(item)
            if rec:
                records.append(rec)
        return records

    @staticmethod
    def normalize_one(item: dict[str, Any]) -> FormationRecord | None:
        formation_id = _clean(item.get("formation_id"))
        institution = _clean(item.get("institution"))
        program = _clean(item.get("program"))
        degree = _clean(item.get("degree"))
        location = _clean(item.get("location"))
        description = _clean(item.get("description"))

        courses = _to_str_list(item.get("courses"))
        course_categories = _normalize_course_categories(item.get("course_categories"))
        achievements = _to_str_list(item.get("achievements"))
        tags = _to_str_list(item.get("tags"))
        if not description and achievements:
            description = achievements[0]

        if not courses and course_categories:
            courses = _flatten_course_categories(course_categories)

        if not institution or not program:
            LOGGER.warning("Skipping invalid formation (missing institution/program): %s", item)
            return None

        return FormationRecord(
            formation_id=formation_id or _stable_formation_id(institution, program, item.get("start_date")),
            institution=institution,
            program=program,
            degree=degree or "",
            location=location or "",
            start_date=_normalize_date(item.get("start_date")),
            end_date=_normalize_date(item.get("end_date")),
            is_current=bool(item.get("is_current", False)),
            description=description or "",
            courses=courses,
            course_categories=course_categories,
            achievements=achievements,
            tags=tags,
        )


class FormationRepositoryGateway:
    """DB gateway for formations writes."""

    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = db_path.resolve()
        self.schema_path = schema_path.resolve()

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='formations'"
            ).fetchone()
            if not table_exists:
                if not self.schema_path.exists():
                    raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

                LOGGER.info("formations missing, initializing schema from %s", self.schema_path)
                conn.executescript(self.schema_path.read_text(encoding="utf-8"))
                conn.commit()
                return

            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(formations)").fetchall()
            }
            if "course_categories_json" not in columns:
                LOGGER.info("Adding missing column course_categories_json to formations")
                conn.execute(
                    "ALTER TABLE formations ADD COLUMN course_categories_json TEXT NOT NULL DEFAULT '{}'"
                )
                conn.commit()

    def upsert_many(self, records: list[FormationRecord]) -> tuple[int, int]:
        sql = """
        INSERT INTO formations (
            formation_id,
            institution,
            program,
            degree,
            location,
            start_date,
            end_date,
            is_current,
            description,
            courses_json,
            course_categories_json,
            achievements_json,
            tags_json
        ) VALUES (
            :formation_id,
            :institution,
            :program,
            :degree,
            :location,
            :start_date,
            :end_date,
            :is_current,
            :description,
            :courses_json,
            :course_categories_json,
            :achievements_json,
            :tags_json
        )
        ON CONFLICT(formation_id) DO UPDATE SET
            institution = excluded.institution,
            program = excluded.program,
            degree = excluded.degree,
            location = excluded.location,
            start_date = excluded.start_date,
            end_date = excluded.end_date,
            is_current = excluded.is_current,
            description = excluded.description,
            courses_json = excluded.courses_json,
            course_categories_json = excluded.course_categories_json,
            achievements_json = excluded.achievements_json,
            tags_json = excluded.tags_json,
            indexed_at = CURRENT_TIMESTAMP
        """

        inserted = 0
        updated = 0

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            for record in records:
                existed = conn.execute(
                    "SELECT 1 FROM formations WHERE formation_id = ?",
                    (record.formation_id,),
                ).fetchone()

                conn.execute(
                    sql,
                    {
                        "formation_id": record.formation_id,
                        "institution": record.institution,
                        "program": record.program,
                        "degree": record.degree,
                        "location": record.location,
                        "start_date": record.start_date,
                        "end_date": record.end_date,
                        "is_current": int(record.is_current),
                        "description": record.description,
                        "courses_json": json.dumps(record.courses, ensure_ascii=True),
                        "course_categories_json": json.dumps(
                            record.course_categories,
                            ensure_ascii=True,
                            sort_keys=True,
                        ),
                        "achievements_json": json.dumps(record.achievements, ensure_ascii=True),
                        "tags_json": json.dumps(record.tags, ensure_ascii=True),
                    },
                )

                if existed:
                    updated += 1
                else:
                    inserted += 1

            conn.commit()

        return inserted, updated


class LatexFormationTemplateWriter:
    """Builds and writes the LaTeX section for formations."""

    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path.resolve()

    def write(self, records: list[FormationRecord]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        latex = self._build_latex(records)
        self.output_path.write_text(latex, encoding="utf-8")

    def _build_latex(self, records: list[FormationRecord]) -> str:
        lines: list[str] = []
        lines.append("% Auto-generated by formations_orchestrator")
        lines.append("\\section*{Formation}")
        lines.append("\\begin{itemize}")

        for rec in records:
            period = _format_period(rec.start_date, rec.end_date, rec.is_current)
            header = f"\\textbf{{{_latex_escape(rec.program)}}}"
            inst = _latex_escape(rec.institution)
            degree = _latex_escape(rec.degree) if rec.degree else ""
            location = _latex_escape(rec.location) if rec.location else ""

            detail_parts = [p for p in [inst, degree, location, period] if p]
            detail = " -- ".join(detail_parts)

            lines.append(f"  \\item {header}\\")
            lines.append(f"  {detail}\\")

            if rec.description:
                lines.append(f"  \\emph{{{_latex_escape(rec.description)}}}")

            if rec.course_categories:
                category_parts = []
                for category, category_courses in rec.course_categories.items():
                    preview = ", ".join(category_courses[:3])
                    if len(category_courses) > 3:
                        preview = f"{preview}, ..."
                    category_parts.append(f"{category}: {preview}")
                category_line = " ; ".join(category_parts)
                lines.append(f"  \\newline \\small { _latex_escape(category_line) }")

        lines.append("\\end{itemize}")
        lines.append("")
        return "\n".join(lines)


class FormationsTemplateOrchestrator:
    """4-layer orchestration for formations -> DB + LaTeX template output."""

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        db_path: Path,
        schema_path: Path,
        dry_run: bool = False,
    ) -> None:
        self.input_path = input_path.resolve()
        self.output_path = output_path.resolve()
        self.dry_run = dry_run
        self.reader = FormationSourceReader(self.input_path)
        self.gateway = FormationRepositoryGateway(db_path=db_path, schema_path=schema_path)
        self.writer = LatexFormationTemplateWriter(self.output_path)

    def run(self) -> None:
        LOGGER.info("Starting formations orchestration from %s", self.input_path)

        raw_items = self.reader.read()
        LOGGER.info("Ingestion layer: %d raw records", len(raw_items))

        records = FormationNormalizer.normalize_many(raw_items)
        LOGGER.info("Normalization/validation layer: %d valid records", len(records))

        if self.dry_run:
            LOGGER.info("Dry-run enabled: no database write and no LaTeX file will be written")
            return

        self.gateway.ensure_schema()
        inserted, updated = self.gateway.upsert_many(records)
        LOGGER.info(
            "Persistence layer complete: inserted=%d updated=%d total=%d",
            inserted,
            updated,
            len(records),
        )

        self.writer.write(records)
        LOGGER.info("Output layer complete: %s", self.output_path)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return parts
    return []


def _normalize_course_categories(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, list[str]] = {}
    for raw_category, raw_courses in value.items():
        category = str(raw_category).strip()
        if not category:
            continue
        courses = _to_str_list(raw_courses)
        if courses:
            normalized[category] = courses
    return normalized


def _flatten_course_categories(course_categories: dict[str, list[str]]) -> list[str]:
    flattened: list[str] = []
    for category_courses in course_categories.values():
        flattened.extend(category_courses)
    return sorted(set(flattened))


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    for pattern in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(text, pattern)
            if pattern == "%Y":
                return f"{parsed.year:04d}-01-01"
            if pattern == "%Y-%m":
                return f"{parsed.year:04d}-{parsed.month:02d}-01"
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _stable_formation_id(institution: str, program: str, start_date: Any) -> str:
    normalized_start = _normalize_date(start_date) or "unknown"
    seed = f"{institution.lower()}|{program.lower()}|{normalized_start}"
    return str(uuid5(NAMESPACE_URL, seed))


def _format_period(start_date: str | None, end_date: str | None, is_current: bool) -> str:
    if not start_date and not end_date:
        return ""
    if is_current:
        return f"{start_date or '?'} - present"
    if start_date and end_date:
        return f"{start_date} - {end_date}"
    if start_date:
        return f"since {start_date}"
    return end_date or ""


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    escaped = text
    for old, new in replacements.items():
        escaped = escaped.replace(old, new)
    return escaped


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate LaTeX formation section from standardized JSON/Markdown input"
    )
    parser.add_argument(
        "--input-path",
        default="data/formations/linkedin_charly_romy_tanga_formations.json",
        help="Source input file (.json or .md)",
    )
    parser.add_argument(
        "--output-path",
        default="templates/formations/formation_section.tex",
        help="Generated LaTeX output path",
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
    parser.add_argument("--dry-run", action="store_true", help="Run without writing output file")
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

    orchestrator = FormationsTemplateOrchestrator(
        input_path=Path(args.input_path),
        output_path=Path(args.output_path),
        db_path=Path(args.db_path),
        schema_path=Path(args.schema_path),
        dry_run=args.dry_run,
    )

    try:
        orchestrator.run()
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("formations orchestration failed")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
