from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import ARCHIVE_DIR, INDEX_PATH, REPO_ROOT, repo_relative


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_artifact_type(path: Path) -> str:
    name = path.stem.lower()
    if name.startswith("lm_"):
        return "cover_letter"
    return "cv"


def infer_language(path: Path) -> str:
    parts = path.stem.lower().split("_")
    if len(parts) > 1 and len(parts[1]) in (2, 5):
        return parts[1]
    for candidate in path.parts:
        if candidate.lower() in {"fr", "en", "de", "it", "es"}:
            return candidate.lower()
    return "unknown"


def build_generation_id(path: Path) -> str:
    relative = repo_relative(path).replace("/", "-")
    return slugify(relative)


def artifact_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "generation_id": build_generation_id(path),
        "type": infer_artifact_type(path),
        "language": infer_language(path),
        "filename": path.name,
        "path": repo_relative(path),
        "size_bytes": stat.st_size,
        "timestamp": int(stat.st_mtime),
        "hash_sha256": sha256sum(path),
        "source": "archive-scan",
    }


def scan_archive(root: Path | None = None) -> list[dict[str, Any]]:
    archive_root = (root or ARCHIVE_DIR).resolve()
    if not archive_root.exists():
        return []
    return [artifact_record(path) for path in sorted(archive_root.rglob("*.pdf"))]


def write_index(records: list[dict[str, Any]], destination: Path | None = None) -> Path:
    dest = destination or INDEX_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return dest


@dataclass
class ValidationIssue:
    level: str
    message: str
    path: str | None = None
