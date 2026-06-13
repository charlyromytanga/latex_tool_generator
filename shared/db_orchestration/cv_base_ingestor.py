"""
cv_base_ingestor.py
-------------------
Lit les fichiers sources depuis docs/cv_base/*.json
et peuple la table cv_base via DatabaseManager.

Format attendu des JSON sources : voir docs/cv_base/cv_base_fr.json

Colonnes de la table cv_base :
    id, language, header, summary, skills, experience, education,
    certifications, projects, languages, interests, target_titles

Convention de sérialisation :
    - Les champs texte multi-lignes sont sérialisés en bullet "• item\n"
    - target_titles : liste → chaîne séparée par ";"
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

LOGGER = logging.getLogger(__name__)

# Chemin racine du dépôt (2 niveaux au-dessus de shared/)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCS_CV_BASE = _REPO_ROOT / "docs" / "cv_base"
_DEFAULT_DB_PATH = _REPO_ROOT / "backend" / "db" / "jobcv.db"


# ---------------------------------------------------------------------------
# Sérialiseurs : JSON riche → texte bullet pour la table
# ---------------------------------------------------------------------------

def _bullets(items: List[str]) -> str:
    """['a', 'b'] → ' a\n b'"""
    return "\n".join(f" {i}" for i in items if i)


def _serialize_summary(data: List[str]) -> str:
    return _bullets(data)


def _serialize_skills(data: Dict[str, List[str]]) -> str:
    """Uniquement soft"""
    #all_items = data.get("soft", []) + data.get("technical", [])
    all_items = data.get("soft", [])
    return _bullets(all_items)


def _serialize_technical(data: Dict[str, List[str]]) -> str:
    """Prend technical pour les compétences."""
    all_items = data.get("technical", [])
    return _bullets(all_items)


def _serialize_experience(data: List[Dict[str, Any]]) -> str:
    lines = []
    for exp in data:
        role    = exp.get("role", "")
        realisation    = exp.get("realisation", "")
        company = exp.get("company", "")
        loc     = exp.get("location", "")
        period   = exp.get("periode", "")
        desc    = exp.get("description", "")
        header_parts = [part for part in (role, realisation, company, loc, period, desc) if part]
        header = " | ".join(header_parts)
        lines.append(header)
    return "\n".join(lines)


def _serialize_education(data: List[Dict[str, Any]]) -> str:
    """Serialize education with degree, field, school, location, period and description."""
    lines = []
    for edu in data:
        degree   = edu.get("degree", "")
        field    = edu.get("field", "")
        school   = edu.get("school", "")
        location = edu.get("location", "")
        desc     = edu.get("description", "")
        period    = edu.get("periode", "")

        header_parts = [part for part in (degree, field, school, location, period, desc) if part]
        header = " | ".join(header_parts)
        """
        if location:
            header = f"{header} — {location}" if header else location
        if period:
            header = f"{period} : {header}" if header else period

        if header and desc:
            lines.append(f"{header}. {desc}")
        elif header:
            lines.append(f"{header}.")
        elif desc:
            lines.append(desc)
        """        
        lines.append(header)
    return "\n".join(lines)


def _serialize_certifications(data: List[Dict[str, Any]]) -> str:
    parts = []
    for cert in data:
        name   = cert.get("name", "")
        status = cert.get("status", "")
        parts.append(f"{name} ({status})" if status else name)
    return ", ".join(parts)


def _serialize_projects(data: List[Dict[str, Any]]) -> str:
    lines = []
    for proj in data:
        ref = proj.get("ref", "")
        title = proj.get("title", "")
        mots_cles = proj.get("Mots-clés", [])
        period = proj.get("periode", "")
        desc  = proj.get("description", "")

        # Conversion lite en string
        if isinstance(mots_cles, list):
            mots_cles = ", ".join(mots_cles)
            
        header_parts = [part for part in (ref, title, mots_cles, period, desc) if part]
        header = " | ".join(header_parts)
        lines.append(header)

    return "\n".join(lines)


def _serialize_languages(data: List[Dict[str, Any]]) -> str:
    parts = [f"{l.get('name', '')} : {l.get('level', '')}" for l in data]
    return " ; ".join(parts)


def _serialize_interests(data: List[str]) -> str:
    return ", ".join(data)


def _serialize_header(data: Dict[str, Any]) -> str:
    name     = data.get("name", "")
    location = data.get("location", "")
    phone    = data.get("phone", "")
    email    = data.get("email", "")
    linkedin = data.get("linkedin", "")
    return f"<POSTE>\n{name}\n{location} | {phone} | {email} | {linkedin}"


def _serialize_target_titles(data: List[str]) -> str:
    return "\n".join(data)


# ---------------------------------------------------------------------------
# Dataclass miroir de la table cv_base
# ---------------------------------------------------------------------------

@dataclass
class CVBaseRecord:
    id: str
    language: str
    header: str
    summary: str
    skills: str
    experience: str
    education: str
    technical: str
    certifications: str
    projects: str
    languages: str
    interests: str
    target_titles: str


# ---------------------------------------------------------------------------
# Lecteur de source JSON
# ---------------------------------------------------------------------------

class CVBaseSourceReader:
    """Charge et valide un fichier JSON source cv_base."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> Dict[str, Any]:
        if not self.path.exists():
            raise FileNotFoundError(f"Source non trouvée : {self.path}")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for req in ("id", "language"):
            if not data.get(req):
                raise ValueError(f"Champ requis manquant '{req}' dans {self.path}")
        return data


# ---------------------------------------------------------------------------
# Convertisseur JSON → CVBaseRecord
# ---------------------------------------------------------------------------

class CVBaseConverter:
    """Convertit un dict JSON riche en CVBaseRecord sérialisé (texte bullet)."""

    def convert(self, data: Dict[str, Any]) -> CVBaseRecord:
        return CVBaseRecord(
            id             = data["id"],
            language       = data["language"],
            header         = _serialize_header(data.get("header", {})),
            summary        = _serialize_summary(data.get("summary", [])),
            skills         = _serialize_skills(data.get("skills", {})),
            experience     = _serialize_experience(data.get("experience", [])),
            education      = _serialize_education(data.get("education", [])),
            technical      = _serialize_technical(data.get("skills", {})),
            certifications = _serialize_certifications(data.get("certifications", [])),
            projects       = _serialize_projects(data.get("projects", [])),
            languages      = _serialize_languages(data.get("languages", [])),
            interests      = _serialize_interests(data.get("interests", [])),
            target_titles  = _serialize_target_titles(data.get("target_titles", [])),
        )


# ---------------------------------------------------------------------------
# Orchestrateur principal
# ---------------------------------------------------------------------------

class CVBaseIngestionOrchestrator:
    """
    Orchestre la lecture des JSON sources et l'insertion dans cv_base via DatabaseManager.

    Usage :
        orch = CVBaseIngestionOrchestrator(db_path="/path/to/jobcv.db")
        result = orch.run_from_file(Path("docs/cv_base/cv_base_fr.json"))
        results = orch.run_all(docs_dir=Path("docs/cv_base"))
    """

    def __init__(self, db_path: Path | str = _DEFAULT_DB_PATH) -> None:
        # Import local pour éviter la dépendance circulaire si utilisé hors du projet
        sys.path.insert(0, str(_REPO_ROOT))
        from backend.services.cv.core.cv_utils import DatabaseManager  # type: ignore
        self.db = DatabaseManager(str(db_path))
        self.converter = CVBaseConverter()

    def run_from_file(self, source_path: Path) -> Dict[str, Any]:
        """
        Ingère un seul fichier JSON source dans cv_base.
        Si l'enregistrement existe déjà, il est supprimé puis réinséré.

        Returns:
            {"id": ..., "language": ..., "status": "inserted"|"replaced"} ou {"error": ...}
        """
        LOGGER.info("Ingestion cv_base ← %s", source_path)
        try:
            data   = CVBaseSourceReader(source_path).read()
            record = self.converter.convert(data)

            existing = self.db.get_cv_base(record.id)
            if existing:
                self.db.delete_cv_base(record.id)
                LOGGER.info("cv_base supprimé avant réinsertion → id=%s", record.id)
                status = "replaced"
            else:
                status = "inserted"

            self.db.add_cv_base({
                "id":            record.id,
                "language":      record.language,
                "header":        record.header,
                "summary":       record.summary,
                "skills":        record.skills,
                "experience":    record.experience,
                "education":     record.education,
                "technical":     record.technical,
                "certifications": record.certifications,
                "projects":      record.projects,
                "languages":     record.languages,
                "interests":     record.interests,
                "target_titles": record.target_titles,
            })
            LOGGER.info("cv_base %s → id=%s lang=%s", status, record.id, record.language)
            return {"id": record.id, "language": record.language, "status": status}
        except Exception as exc:
            LOGGER.exception("Erreur ingestion %s : %s", source_path, exc)
            return {"file": str(source_path), "error": str(exc)}

    def run_all(self, docs_dir: Path = _DOCS_CV_BASE) -> List[Dict[str, Any]]:
        """
        Ingère tous les fichiers *.json présents dans docs_dir.

        Returns:
            Liste de résultats par fichier.
        """
        files = sorted(docs_dir.glob("*.json"))
        if not files:
            LOGGER.warning("Aucun fichier JSON trouvé dans %s", docs_dir)
            return []
        results = [self.run_from_file(f) for f in files]
        inserted  = sum(1 for r in results if r.get("status") == "inserted")
        replaced  = sum(1 for r in results if r.get("status") == "replaced")
        err       = sum(1 for r in results if "error" in r)
        LOGGER.info(
            "cv_base ingestion terminée : %d inséré(s), %d remplacé(s), %d erreur(s)",
            inserted, replaced, err,
        )
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Ingestion cv_base depuis docs/cv_base/*.json")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        type=Path,
        help="Fichier JSON source (optionnel — si absent, ingère tous les fichiers de docs/cv_base/)",
    )
    parser.add_argument(
        "--db-path",
        default=str(_DEFAULT_DB_PATH),
        help=f"Chemin vers jobcv.db (défaut : {_DEFAULT_DB_PATH})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = _build_parser().parse_args(argv)
    orch = CVBaseIngestionOrchestrator(db_path=args.db_path)

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
