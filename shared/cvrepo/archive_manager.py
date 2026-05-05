from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .metadata import infer_artifact_type


@dataclass
class ArchivedFile:
    source: Path
    destination: Path


def archive_pdfs(pdf_paths: list[Path], archive_root: Path, delete_source: bool = False) -> list[ArchivedFile]:
    archived: list[ArchivedFile] = []
    for pdf_path in sorted(pdf_paths):
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            continue
        timestamp = datetime.fromtimestamp(pdf_path.stat().st_mtime)
        artifact_type = infer_artifact_type(pdf_path)
        destination_dir = archive_root / artifact_type / f"{timestamp:%Y}" / f"{timestamp:%m}"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / pdf_path.name
        shutil.copy2(pdf_path, destination)
        if delete_source:
            pdf_path.unlink()
        archived.append(ArchivedFile(source=pdf_path, destination=destination))
    return archived


def archive_rendered_pdfs(source_dir: Path, archive_root: Path, delete_source: bool = False) -> list[ArchivedFile]:
    if not source_dir.exists():
        return []
    return archive_pdfs(sorted(source_dir.glob("*.pdf")), archive_root, delete_source=delete_source)
