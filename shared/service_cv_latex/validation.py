from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .job_parser import infer_offer_metadata
from .metadata import ValidationIssue


REQUIRED_OFFER_KEYS = {"offer_id", "company", "role_title", "location", "tier"}
REQUIRED_ARTIFACT_KEYS = {"generation_id", "type", "language", "filename", "path"}


def validate_offer_metadata(data: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = REQUIRED_OFFER_KEYS - set(data)
    for key in sorted(missing):
        issues.append(ValidationIssue(level="warning", message=f"Missing metadata key: {key}"))
    if "location" in data and not isinstance(data["location"], dict):
        issues.append(ValidationIssue(level="warning", message="location should be an object"))
    return issues


def validate_artifact_record(data: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    missing = REQUIRED_ARTIFACT_KEYS - set(data)
    for key in sorted(missing):
        issues.append(ValidationIssue(level="warning", message=f"Missing artifact key: {key}"))
    return issues


def validate_offer_tree(offers_root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for offer_path in sorted(offers_root.rglob("*.md")):
        if offer_path.name in {"README.md", "STRUCTURE.md", "offer_template.md"}:
            continue
        if "_templates" in offer_path.parts:
            continue
        metadata_path = offer_path.with_suffix(".metadata.json")
        if metadata_path.exists():
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            for issue in validate_offer_metadata(data):
                issue.path = str(metadata_path)
                issues.append(issue)
        else:
            inferred = infer_offer_metadata(offer_path, offers_root)
            issues.append(
                ValidationIssue(
                    level="info",
                    message=f"No metadata file yet, inferred offer_id={inferred['offer_id']}",
                    path=str(offer_path),
                )
            )
    return issues
