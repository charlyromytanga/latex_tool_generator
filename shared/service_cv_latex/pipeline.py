from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .archive_manager import ArchivedFile, archive_pdfs
from .job_parser import analyze_text, infer_offer_metadata
from .metadata import scan_archive, slugify, write_index
from .paths import ARCHIVE_DIR, OFFERS_DIR, RENDER_DIR, SUMMARIES_DIR
from .template_engine import default_letter_template, default_template, render_letter, render_summary


@dataclass
class GenerationResult:
    summary: Path
    cv: Path | None
    letter: Path | None
    archived: list[ArchivedFile]
    index: Path | None


def build_offer_summary(offer_path: Path, offers_root: Path = OFFERS_DIR) -> dict[str, Any]:
    summary = analyze_text(offer_path.read_text(encoding="utf-8"))
    try:
        metadata = infer_offer_metadata(offer_path, offers_root)
    except ValueError:
        metadata = {
            "offer_id": slugify(offer_path.stem),
            "path": str(offer_path),
            "company": "unknown",
            "role_slug": offer_path.stem,
            "source_format": offer_path.suffix.lower(),
        }
    for key, value in metadata.items():
        if value and not summary.get(key):
            summary[key] = value
    if summary.get("city") and not summary.get("location"):
        summary["location"] = summary["city"]
    return summary


def write_summary(summary: dict[str, Any], offer_path: Path, output_dir: Path = SUMMARIES_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{offer_path.stem}_summary.json"
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def generate_application(
    offer_path: Path,
    language: str = "fr",
    kind: str = "both",
    output_dir: Path = RENDER_DIR,
    summaries_dir: Path = SUMMARIES_DIR,
    archive: bool = False,
    archive_root: Path = ARCHIVE_DIR,
) -> GenerationResult:
    summary = build_offer_summary(offer_path)
    summary_path = write_summary(summary, offer_path, summaries_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    cv_path: Path | None = None
    letter_path: Path | None = None
    generated_paths: list[Path] = []

    if kind in {"both", "cv"}:
        cv_path = render_summary(
            summary_path=summary_path,
            template_dir=default_template(language),
            output_dir=output_dir,
            prefix=f"cv_{language}_{offer_path.stem}",
        )
        generated_paths.append(cv_path)

    if kind in {"both", "letter"}:
        letter_path = render_letter(
            summary_path=summary_path,
            template_dir=default_letter_template(language),
            language=language,
            output_dir=output_dir,
            prefix=f"lm_{language}_{offer_path.stem}",
        )
        generated_paths.append(letter_path)

    archived: list[ArchivedFile] = []
    index_path: Path | None = None
    if archive and generated_paths:
        archived = archive_pdfs(generated_paths, archive_root)
        index_path = write_index(scan_archive(archive_root), destination=archive_root / "index.jsonl")

    return GenerationResult(summary=summary_path, cv=cv_path, letter=letter_path, archived=archived, index=index_path)