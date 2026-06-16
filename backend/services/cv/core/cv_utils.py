import os
import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, Optional, Set, Tuple
try:
    from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications  # noqa: F401
except ImportError:
    db = CVBase = Jobs = CVApplications = Applications = None  # type: ignore


def _get_flask_db():
    """Returns the Flask-SQLAlchemy db object if inside a Flask app context, else None."""
    if db is None or CVBase is None:
        return None
    try:
        from flask import current_app
        current_app._get_current_object()
        return db
    except (RuntimeError, ImportError):
        return None


_MODEL_MAP: Dict[str, Any] = {}


def _model_map() -> Dict[str, Any]:
    if CVBase is not None and not _MODEL_MAP:
        _MODEL_MAP.update({
            "cv_base": CVBase,
            "jobs": Jobs,
            "cv_applications": CVApplications,
            "applications": Applications,
        })
    return _MODEL_MAP

import logging
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# --- Classe pour la gestion des tables dans la base de données ---
# ---------------------------------------------------------------------------

class DatabaseManager:
    """
    Gère les interactions avec la base de données SQLite : création, lecture,
    mise à jour, suppression des enregistrements dans les tables :
        cv_base, jobs, cv_applications, applications.

    Utilisation standalone (sans Flask) :
        db = DatabaseManager("/path/to/jobcv.db")
        db.add_job({"id": "offer-xyz", "language": "FR", "country": "France", ...})
        job = db.get_job("offer-xyz")
        db.update_job("offer-xyz", city="Lyon", job_title="Data Analyst")
        db.delete_job("offer-xyz")
        jobs = db.list_jobs()
    """

    # Colonnes attendues par table (ordre d'INSERT)
    _COLUMNS: Dict[str, List[str]] = {
        "cv_base": [
            "id", "language", "header", "summary", "skills",
            "experience", "education", "technical", "certifications", "projects",
            "languages", "interests", "target_titles",
        ],
        "jobs": [
            "id", "language", "country", "city", "company_name",
            "company_type", "offer_description", "company_presentation", "job_title",
        ],
        "cv_applications": [
            "id", "language", "header", "summary", "skills",
            "experience", "education", "certifications", "projects",
            "languages", "interests", "job_offer_id", "cv_base_id",
            "matching_score", "generation_date",
        ],
        "applications": [
            "id", "job_offer_id", "cv_base_id", "lm", "matching_score",
            "generation_date", "mail_content", "days_to_wait", "response_email",
        ],
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._sa = _get_flask_db()

    # ------------------------------------------------------------------
    # Helpers internes — SQLAlchemy (Flask/Supabase) ou SQLite (CLI)
    # ------------------------------------------------------------------

    @staticmethod
    def _obj_to_dict(obj: Any) -> Dict[str, Any]:
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row else None

    def _upsert(self, table: str, data: Dict[str, Any]) -> None:
        if self._sa is not None:
            model_cls = _model_map()[table]
            existing = self._sa.session.get(model_cls, data.get("id"))
            if existing:
                for k, v in data.items():
                    if hasattr(existing, k):
                        setattr(existing, k, v)
            else:
                obj = model_cls(**{k: v for k, v in data.items() if hasattr(model_cls, k)})
                self._sa.session.add(obj)
            self._sa.session.commit()
            return
        cols = [c for c in self._COLUMNS[table] if c in data]
        if not cols:
            raise ValueError(f"Aucune colonne valide fournie pour la table '{table}'")
        placeholders = ", ".join("?" for _ in cols)
        col_list = ", ".join(cols)
        values = [data[c] for c in cols]
        sql = f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})"
        with self._connect() as conn:
            conn.execute(sql, values)

    def _update(self, table: str, record_id: str, **fields: Any) -> int:
        if self._sa is not None:
            model_cls = _model_map()[table]
            obj = self._sa.session.get(model_cls, record_id)
            if not obj:
                return 0
            for k, v in fields.items():
                if hasattr(obj, k) and k != "id":
                    setattr(obj, k, v)
            self._sa.session.commit()
            return 1
        valid = {k: v for k, v in fields.items() if k in self._COLUMNS[table] and k != "id"}
        if not valid:
            raise ValueError(f"Aucun champ valide à mettre à jour dans '{table}'")
        set_clause = ", ".join(f"{k} = ?" for k in valid)
        values = list(valid.values()) + [record_id]
        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        with self._connect() as conn:
            cur = conn.execute(sql, values)
            return cur.rowcount

    def _get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        if self._sa is not None:
            obj = self._sa.session.get(_model_map()[table], record_id)
            return self._obj_to_dict(obj) if obj else None
        with self._connect() as conn:
            cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            return self._row_to_dict(cur.fetchone())

    def _delete(self, table: str, record_id: str) -> int:
        if self._sa is not None:
            obj = self._sa.session.get(_model_map()[table], record_id)
            if not obj:
                return 0
            self._sa.session.delete(obj)
            self._sa.session.commit()
            return 1
        with self._connect() as conn:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            return cur.rowcount

    def _list(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self._sa is not None:
            model_cls = _model_map()[table]
            query = self._sa.session.query(model_cls)
            if filters:
                for k, v in filters.items():
                    query = query.filter(getattr(model_cls, k) == v)
            return [self._obj_to_dict(obj) for obj in query.all()]
        sql = f"SELECT * FROM {table}"
        values: List[Any] = []
        if filters:
            where = " AND ".join(f"{k} = ?" for k in filters)
            sql += f" WHERE {where}"
            values = list(filters.values())
        with self._connect() as conn:
            cur = conn.execute(sql, values)
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Table : cv_base
    # ------------------------------------------------------------------

    def add_cv_base(self, data: Dict[str, Any]) -> None:
        """Insère ou remplace un enregistrement dans cv_base.
        data doit contenir au minimum 'id' et 'language'."""
        if not data.get("id") or not data.get("language"):
            raise ValueError("cv_base requiert 'id' et 'language'")
        self._upsert("cv_base", data)
        logger.info("[DB] cv_base upsert → %s", data["id"])

    def get_cv_base(self, cv_base_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le dict d'un enregistrement cv_base ou None."""
        return self._get("cv_base", cv_base_id)

    def update_cv_base(self, cv_base_id: str, **fields: Any) -> int:
        """Met à jour les champs donnés dans cv_base. Retourne le nombre de lignes modifiées."""
        n = self._update("cv_base", cv_base_id, **fields)
        logger.info("[DB] cv_base update → %s (%d ligne(s))", cv_base_id, n)
        return n

    def delete_cv_base(self, cv_base_id: str) -> int:
        """Supprime un enregistrement cv_base. Retourne le nombre de lignes supprimées."""
        n = self._delete("cv_base", cv_base_id)
        logger.info("[DB] cv_base delete → %s (%d ligne(s))", cv_base_id, n)
        return n

    def list_cv_bases(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liste tous les enregistrements cv_base, avec filtre optionnel par langue."""
        filters = {"language": language} if language else None
        return self._list("cv_base", filters)

    # ------------------------------------------------------------------
    # Table : jobs
    # ------------------------------------------------------------------

    def add_job(self, data: Dict[str, Any]) -> None:
        """Insère ou remplace une offre d'emploi dans jobs.
        data doit contenir au minimum 'id', 'language' et 'country'."""
        for req in ("id", "language", "country"):
            if not data.get(req):
                raise ValueError(f"jobs requiert le champ '{req}'")
        self._upsert("jobs", data)
        logger.info("[DB] jobs upsert → %s (%s)", data["id"], data.get("company_name", ""))

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le dict d'une offre ou None."""
        return self._get("jobs", job_id)

    def update_job(self, job_id: str, **fields: Any) -> int:
        """Met à jour les champs donnés dans jobs. Retourne le nombre de lignes modifiées."""
        n = self._update("jobs", job_id, **fields)
        logger.info("[DB] jobs update → %s (%d ligne(s))", job_id, n)
        return n

    def delete_job(self, job_id: str) -> int:
        """Supprime une offre. Retourne le nombre de lignes supprimées."""
        n = self._delete("jobs", job_id)
        logger.info("[DB] jobs delete → %s (%d ligne(s))", job_id, n)
        return n

    def list_jobs(self, language: Optional[str] = None, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liste toutes les offres, avec filtres optionnels."""
        filters: Dict[str, Any] = {}
        if language:
            filters["language"] = language
        if company_name:
            filters["company_name"] = company_name
        return self._list("jobs", filters or None)

    # ------------------------------------------------------------------
    # Table : cv_applications
    # ------------------------------------------------------------------

    def add_cv_application(self, data: Dict[str, Any]) -> None:
        """Insère ou remplace un CV adapté à une offre dans cv_applications.
        data doit contenir 'id', 'language', 'job_offer_id', 'cv_base_id'."""
        for req in ("id", "language", "job_offer_id", "cv_base_id"):
            if not data.get(req):
                raise ValueError(f"cv_applications requiert le champ '{req}'")
        self._upsert("cv_applications", data)
        logger.info("[DB] cv_applications upsert → %s", data["id"])

    def get_cv_application(self, cv_app_id: str) -> Optional[Dict[str, Any]]:
        return self._get("cv_applications", cv_app_id)

    def update_cv_application(self, cv_app_id: str, **fields: Any) -> int:
        n = self._update("cv_applications", cv_app_id, **fields)
        logger.info("[DB] cv_applications update → %s (%d ligne(s))", cv_app_id, n)
        return n

    def delete_cv_application(self, cv_app_id: str) -> int:
        n = self._delete("cv_applications", cv_app_id)
        logger.info("[DB] cv_applications delete → %s (%d ligne(s))", cv_app_id, n)
        return n

    def list_cv_applications(
        self,
        cv_base_id: Optional[str] = None,
        job_offer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Liste les CV applications, filtrables par cv_base_id et/ou job_offer_id."""
        filters: Dict[str, Any] = {}
        if cv_base_id:
            filters["cv_base_id"] = cv_base_id
        if job_offer_id:
            filters["job_offer_id"] = job_offer_id
        return self._list("cv_applications", filters or None)

    # ------------------------------------------------------------------
    # Table : applications
    # ------------------------------------------------------------------

    def add_application(self, data: Dict[str, Any]) -> None:
        """Insère ou remplace une candidature dans applications.
        data doit contenir 'id', 'job_offer_id', 'cv_base_id'."""
        for req in ("id", "job_offer_id", "cv_base_id"):
            if not data.get(req):
                raise ValueError(f"applications requiert le champ '{req}'")
        self._upsert("applications", data)
        logger.info("[DB] applications upsert → %s", data["id"])

    def get_application(self, app_id: str) -> Optional[Dict[str, Any]]:
        return self._get("applications", app_id)

    def update_application(self, app_id: str, **fields: Any) -> int:
        n = self._update("applications", app_id, **fields)
        logger.info("[DB] applications update → %s (%d ligne(s))", app_id, n)
        return n

    def delete_application(self, app_id: str) -> int:
        n = self._delete("applications", app_id)
        logger.info("[DB] applications delete → %s (%d ligne(s))", app_id, n)
        return n

    def list_applications(
        self,
        cv_base_id: Optional[str] = None,
        job_offer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Liste les candidatures, filtrables par cv_base_id et/ou job_offer_id."""
        filters: Dict[str, Any] = {}
        if cv_base_id:
            filters["cv_base_id"] = cv_base_id
        if job_offer_id:
            filters["job_offer_id"] = job_offer_id
        return self._list("applications", filters or None)

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, int]:
        """Retourne le nombre d'enregistrements par table."""
        if self._sa is not None:
            from sqlalchemy import func
            result: Dict[str, int] = {}
            for table, model_cls in _model_map().items():
                result[table] = self._sa.session.query(func.count()).select_from(model_cls).scalar() or 0
            return result
        result = {}
        with self._connect() as conn:
            for table in self._COLUMNS:
                cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
                result[table] = cur.fetchone()[0]
        return result



# ---------------------------------------------------------------------------
# --- Classe pour la gestion des offres enrichies ---
# ---------------------------------------------------------------------------

class JobOfferManager:
    """
    Gère la table job_offer : création, lecture, mise à jour, suppression d'offres enrichies.
    """
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        self.job_offer: dict[str, Any] = {}

    def extract_offer_data(self, offer: Dict[str, str]):
        """Extrait les données pertinentes d'une offre.
            Language str: fr, en
            Country str: fr, uk, lu, de, ch
            City str: string
            Compagny name str: string
            Compagny type str: string (ex: 'grand groupe', 'tpe', 'pme', 'esn', 'banque', 'assurance', 'industrie', 'cabinet conseil')
            Compagny presentation str: string
            Job title str: string
            Job description str: string
        """
        try:
            self.job_offer['language'] = offer.get('language', 'fr')
            self.job_offer['country'] = offer.get('country', 'fr')
            self.job_offer['city'] = offer.get('city', '')
            self.job_offer['compagny_name'] = offer.get('compagny_name', '')
            self.job_offer['compagny_type'] = offer.get('compagny_type', '')
            self.job_offer['compagny_presentation'] = offer.get('compagny_presentation', '')
            self.job_offer['offer_title'] = offer.get('offer_title', '')
            self.job_offer['offer_description'] = offer.get('offer_description', '')
        except Exception as e:
            logger.error(f"Erreur extraction données offre : {e}")
            self.job_offer = {}
        
        def enrich_offer_with_llm(self, offer_data: Dict[str, Any]) :
            """Enrichit une offre d'emploi avec des sections générées par LLM (header, summary, skills, etc.)"""
            enriched_offer = offer_data.copy()
            enriched_offer['llm_header'] = "Exemple de header généré par LLM"
            enriched_offer['llm_summary'] = "Exemple de summary généré par LLM"
            enriched_offer['llm_skills'] = "Exemple de skills générés par LLM"
            return enriched_offer

    def add_offer(self, offer_data: dict):
        """Ajoute une nouvelle offre enrichie dans la base."""
        pass

    def get_offer(self, offer_id: str) :
        """Récupère une offre par son id."""
        pass

    def update_offer(self, offer_id: str, update_data: dict):
        """Met à jour une offre existante."""
        pass

    def delete_offer(self, offer_id: str):
        """Supprime une offre."""
        pass



# ---------------------------------------------------------------------------
# --- Classe pour le suivi des candidatures et génération CV/LM ---
# ---------------------------------------------------------------------------

class CandidatureTracker:
    """
    Gère la table candidature_tracking : suivi, ajout, récupération des candidatures, stockage CV/LM générés.
    """
    def __init__(self, db_dir: str):
        self.db_dir = db_dir

    def add_candidature(self, candidature_data: dict):
        """Ajoute une nouvelle candidature (CV/LM générés, score, etc.)."""
        pass

    def get_candidature(self, candidature_id: str) :
        """Récupère une candidature par son id."""
        pass

    def update_candidature(self, candidature_id: str, update_data: dict):
        """Met à jour une candidature existante."""
        pass

    def delete_candidature(self, candidature_id: str):
        """Supprime une candidature."""
        pass


# ---------------------------------------------------------------------------
# CV LaTeX Generator — modèle _col_gauche / FR
# ---------------------------------------------------------------------------

import os as _os


def _resolve_repo_root() -> Path:
    candidates = []
    project_root_env = _os.getenv("PROJECT_ROOT")
    if project_root_env:
        candidates.append(Path(project_root_env).resolve())
    candidates.append(Path.cwd().resolve())
    module_path = Path(__file__).resolve()
    candidates.extend(module_path.parents)

    for candidate in candidates:
        if (candidate / "backend").exists() and (candidate / "shared").exists():
            return candidate

    return module_path.parents[4]


_REPO_ROOT = _resolve_repo_root()

_TEMPLATE_DIR = Path(
    _os.environ.get(
        "CV_TEMPLATE_DIR",
        str(_REPO_ROOT / "shared" / "service_cv_latex" / "templates" / "_col_gauche"),
    )
)
_OUTPUT_DIR = Path(
    _os.environ.get(
        "CV_OUTPUT_DIR",
        str(_REPO_ROOT / "shared" / "output" / "FR"),
    )
)

_OUTPUT_DIR_BY_LANGUAGE: Dict[str, Path] = {
    "fr": _OUTPUT_DIR,
    "en": Path(
        _os.environ.get(
            "CV_OUTPUT_DIR_EN",
            str(_REPO_ROOT / "shared" / "output" / "EN"),
        )
    ),
}

_DEFAULT_PERSONAL_FR: Dict[str, str] = {
    "name":      "Charly-Romy TANGA",
    "lastname":  "TANGA",
    "firstname": "Charly-Romy",
    "address":   "Paris, France",
    "mail":      "charlyromytanga@gmail.com",
    "phone":     "+33 6 15 42 25 74",
    "linkedin":  "charly-romy-tanga",
    "github":    "charlyromytanga",
    "jobtype":   "Ingénieur en Mathématiques Appliquées Finance et Technologie",
    "disponibilite": "Disponible dès septembre 2026",
}

_DEFAULT_PERSONAL_EN: Dict[str, str] = {
    **_DEFAULT_PERSONAL_FR,
    "jobtype": "Engineer in Applied Mathematics, Finance and Technology",
    "disponibilite": "Available from September 2026",
}

_DEFAULT_PERSONAL_BY_LANGUAGE: Dict[str, Dict[str, str]] = {
    "fr": _DEFAULT_PERSONAL_FR,
    "en": _DEFAULT_PERSONAL_EN,
}

_LABELS_BY_LANGUAGE: Dict[str, Dict[str, str]] = {
    "fr": {
        "availability": r"Disponibilit\'{e}",
        "contact": "Contact",
        "email": "Email",
        "phone": r"T\'{e}l\'{e}phone",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "location": "Adresse",
        "target_position": r"Poste vis\'{e}",
        "strengths": "Atouts",
        "languages": "Langues",
        "interests": r"Centres d'int\'{e}r\^{e}t",
        "search_type": "Type de recherche",
        "skills": r"comp\'{e}tences",
        "technical_skills": r"comp\'{e}tences techniques",
        "experience": r"exp\'{e}riences professionnelles",
        "education": "formation",
        "certifications": "certifications",
        #"projects": r"comp\'{e}tences techniques",
        "projects": r"projets acad\'{e}miques",
        "keywords": r"Mots-cl\'{e}s",
    },
    "en": {
        "availability": "Availability",
        "contact": "Contact",
        "email": "Email",
        "phone": "Phone",
        "linkedin": "LinkedIn",
        "github": "GitHub",
        "location": "Location",
        "target_position": "Target Position",
        "strengths": "Strengths",
        "languages": "Languages",
        "interests": "Interests",
        "search_type": "Target Role",
        "skills": "skills",
        "technical_skills": "technical knowledge",
        "experience": "professional experience",
        "education": "education",
        "certifications": "certifications",
        "projects": "academic projects",
        "keywords": "Keywords",
    },
}


class CVLatexGeneratorBase:
    """
    Generates a French two-column CV PDF from CVBase + Jobs data.

    Usage (standalone, outside Flask):
        gen = CVLatexGeneratorFR.from_db(
            db_path="/app/db/jobcv.db",
            cv_base_id="cv_base_in_all_fr",
            job_id="<job_uuid>",
            max_projects="$Max_PROJECTS",
            max_experiences="$Max_EXPERIENCES",
            max_competences="$Max_COMPETENCES",
            max_competences_techniques="$Max_COMPETENCES_TECHNIQUES",
        )
        tex_path, pdf_path = gen.generate()

    Usage (within Flask, passing model instances):
        cv_dict  = {col: getattr(cv_base_obj, col) for col in CVBase.__table__.columns.keys()}
        job_dict = {col: getattr(job_obj, col) for col in Jobs.__table__.columns.keys()}
        gen = CVLatexGeneratorFR(cv_dict, job_dict)
        tex_path, pdf_path = gen.generate()
    """

    _LANGUAGE = "fr"

    def __init__(
        self,
        cv_base: Dict[str, Any],
        job: Dict[str, Any],
        personal: Optional[Dict[str, str]] = None,
        output_dir: Optional[Path] = None,
        target_title_index: Optional[int] = None,
        max_projects: int = 11,
        max_experiences: int = 8,
        max_competences: int = 7,
        max_competences_techniques: int = 4,
        selected_project_indices: Optional[List[int]] = None,
        selected_experience_indices: Optional[List[int]] = None,
        selected_competence_indices: Optional[List[int]] = None,
        selected_competence_technique_indices: Optional[List[int]] = None,
    ):
        if self._LANGUAGE not in _LABELS_BY_LANGUAGE:
            raise ValueError(f"Unsupported CV language: {self._LANGUAGE}")

        self.cv = cv_base
        self.job = job
        self.language = self._LANGUAGE
        base_personal = _DEFAULT_PERSONAL_BY_LANGUAGE[self.language]
        self.personal = {**base_personal, **(personal or {})}
        self.output_dir = Path(output_dir) if output_dir else _OUTPUT_DIR_BY_LANGUAGE[self.language]
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._gen_date = datetime.now()
        # None  → auto : job_title si disponible dans l'offre, sinon target_titles[0]
        # int   → code 1-based : 1 = premier target_titles, 2 = deuxième, etc.
        self._target_title_index = target_title_index

        # Sélection modulable par section pour adapter le CV à l'offre.
        self.max_projects = max_projects
        self.max_experiences = max_experiences
        self.max_competences = max_competences
        self.max_competences_techniques = max_competences_techniques
        self.selected_project_indices = selected_project_indices
        self.selected_experience_indices = selected_experience_indices
        self.selected_competence_indices = selected_competence_indices
        self.selected_competence_technique_indices = selected_competence_technique_indices

        all_skills = self._normalize_lines(self.cv.get("skills", ""))
        mid = max(1, len(all_skills) // 2)
        self.section_lines: Dict[str, List[str]] = {
            "projects": self._normalize_lines(self.cv.get("projects", "")),
            "experiences": self._normalize_lines(self.cv.get("experience", "")),
            "skills": all_skills,
            "competences": all_skills[:mid],
            #"competences_techniques": all_skills[mid:] if mid > 0 else all_skills,
            "competences_techniques": self._normalize_lines(self.cv.get("technical", ""))
        }

    # ------------------------------------------------------------------
    # Factory: load directly from SQLite (no Flask context needed)
    # ------------------------------------------------------------------

    @classmethod
    def from_db(
        cls,
        db_path: str,
        cv_base_id: str,
        job_id: str,
        personal: Optional[Dict[str, str]] = None,
        output_dir: Optional[Path] = None,
        target_title_index: Optional[int] = None,
        max_projects: int = 11,
        max_experiences: int = 8,
        max_competences: int = 7,
        max_competences_techniques: int = 4,
        selected_project_indices: Optional[List[int]] = None,
        selected_experience_indices: Optional[List[int]] = None,
        selected_competence_indices: Optional[List[int]] = None,
        selected_competence_technique_indices: Optional[List[int]] = None,
    ) -> "CVLatexGeneratorBase":
        """Load CVBase + Jobs rows from SQLite and return a configured instance.

        Args:
            db_path: Path to the SQLite DB.
            cv_base_id: ID of the cv_base row.
            job_id: ID of the jobs row (must exist, even for spontaneous applications —
                    use a placeholder job row with no job_title set).
                        target_title_index: If None (default), use job.job_title when set, else
                                fallback to cv_base.target_titles[0].
                                If an int, interpret it as a 1-based code and pick
                                cv_base.target_titles[target_title_index - 1].
                                    1 → Market Risk Analyst
                                    2 → Trading Analyst
                                    3 → Data Analyst
        """
        flask_db = _get_flask_db()
        if flask_db is not None and CVBase is not None and Jobs is not None:
            cv_obj = flask_db.session.get(CVBase, cv_base_id)
            if cv_obj is None:
                raise ValueError(f"CVBase id '{cv_base_id}' not found")
            job_obj = flask_db.session.get(Jobs, job_id)
            if job_obj is None:
                raise ValueError(f"Job id '{job_id}' not found")
            cv_dict = {c.name: getattr(cv_obj, c.name) for c in cv_obj.__table__.columns}
            job_dict = {c.name: getattr(job_obj, c.name) for c in job_obj.__table__.columns}
        else:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM cv_base WHERE id = ?", (cv_base_id,))
                row_cv = cur.fetchone()
                if row_cv is None:
                    raise ValueError(f"CVBase id '{cv_base_id}' not found in {db_path}")
                cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row_job = cur.fetchone()
                if row_job is None:
                    raise ValueError(f"Job id '{job_id}' not found in {db_path}")
            cv_dict, job_dict = dict(row_cv), dict(row_job)

        return cls(
            cv_base=cv_dict,
            job=job_dict,
            personal=personal,
            output_dir=output_dir,
            target_title_index=target_title_index,
            max_projects=max_projects,
            max_experiences=max_experiences,
            max_competences=max_competences,
            max_competences_techniques=max_competences_techniques,
            selected_project_indices=selected_project_indices,
            selected_experience_indices=selected_experience_indices,
            selected_competence_indices=selected_competence_indices,
            selected_competence_technique_indices=selected_competence_technique_indices,
        )

    def _label(self, key: str) -> str:
        return _LABELS_BY_LANGUAGE[self.language][key]

    def _babel_package_language(self) -> str:
        return "english" if self.language == "en" else "french"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escape(text: str) -> str:
        """Escape LaTeX special characters in plain text."""
        if not text:
            return ""
        replacements = [
            ("\\", r"\textbackslash{}"),
            ("&",  r"\&"),
            ("%",  r"\%"),
            ("$",  r"\$"),
            ("#",  r"\#"),
            ("_",  r"\_"),
            ("{",  r"\{"),
            ("}",  r"\}"),
            ("~",  r"\textasciitilde{}"),
            ("^",  r"\textasciicircum{}"),
        ]
        for char, escaped in replacements:
            text = text.replace(char, escaped)
        return text

    @staticmethod
    def _md_inline(text: str) -> str:
        """Convert inline markdown bold/italic to LaTeX after _escape() has run."""
        text = re.sub(r'(?s)\*\*(.+?)\*\*', r'\\textbf{\1}', text)
        text = re.sub(r'(?s)\*([^*]+?)\*', r'\\textit{\1}', text)
        return text

    @staticmethod
    def _bullets_to_items(text: str, max_items: int = 0, truncate: bool = False) -> str:
        """Convert '• item1\\n• item2' text into LaTeX \\item lines.

        Args:
            text: Source text with optional bullet prefix.
            max_items: If > 0, cap the number of items returned.
            truncate: If True, keep only the first sentence of each item
                      (text before the first '. ' or first 110 chars).
        """
        if not text:
            return r"\item ~"
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("•"):
                line = line[1:].strip()
            if truncate:
                # Keep up to the first period followed by space/end, or 110 chars
                dot_idx = line.find(". ")
                if dot_idx != -1 and dot_idx < 110:
                    line = line[: dot_idx + 1]
                elif len(line) > 110:
                    line = line[:110].rstrip() + "…"
            items.append(r"\item " + line)
        if max_items > 0:
            items = items[:max_items]
        return "\n".join(items) if items else r"\item ~"

    @staticmethod
    def _normalize_lines(value: Any) -> List[str]:
        """Normalize section content into clean plain-text lines."""
        lines: List[str] = []
        if value is None:
            return lines

        if isinstance(value, str):
            raw = value.splitlines()
        elif isinstance(value, list):
            raw = [str(v) for v in value]
        else:
            raw = [str(value)]

        for line in raw:
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^(?:[\-\*•]+\s*)+", "", line).strip()
            if line:
                lines.append(line)
        return lines

    # Normalisation pour une liste
    @staticmethod
    def normalize_keywords(kw : Any):
        if not kw:
            return ""

        if isinstance(kw, list):
            kw = [str(k) for k in kw if k]
        else:
            kw = str(kw).split(",")

        # clean + fix line breaks
        kw = [k.replace("\n", " ").replace("-", "").strip() for k in kw]

        # remove empty + deduplicate light
        kw = [k for k in kw if k]

        return ", ".join(kw)

    # Filtre pour une liste vide
    @staticmethod
    def is_not_empty(val1 : Any, val2 : Any, val3 : Any):
        return bool(val2.strip()) and bool(val3.strip())

    # Traitement dess coupures des mots dans description 
    @staticmethod
    def clean_ocr_text(text: str) -> str:
        if not text:
            return ""

        # 1. supprimer césures type "per-\nformance" ou "per-\n formance"
        text = re.sub(r"-\s*\n\s*", "", text)

        # 2. remplacer retours ligne simples par espace
        text = re.sub(r"\n+", " ", text)

        # 3. normaliser espaces
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()


    @staticmethod
    def _pick_lines(lines: List[str], max_items: int, selected_indices: Optional[List[int]]) -> List[str]:
        """Select relevant lines (optional indices), then apply max_items.

        When selected_indices is provided, it represents an explicit user choice
        and max_items is not applied — the selection itself is the limit.
        When selected_indices is None, max_items caps the result.
        """
        if selected_indices:
            chosen: List[str] = []
            seen: Set[int] = set()
            for idx in selected_indices:
                if idx in seen:
                    continue
                if 0 <= idx < len(lines):
                    chosen.append(lines[idx])
                    seen.add(idx)
            return chosen

        chosen = list(lines)
        if max_items > 0:
            return chosen[:max_items]
        return chosen

    def _filter_text(self, text: str, selected_indices: Optional[List[int]], max_items: int) -> str:
        """Pre-filter a multiline text field by selected indices and max count."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(self._pick_lines(lines, max_items, selected_indices))


    
    def _output_stem(self) -> str:
        mm_yyyy = self._gen_date.strftime("%m_%Y")
        cv_id   = self.cv.get("id", "cv")
        job_id  = self.job.get("id", "job")
        return f"archiv_{job_id}_{cv_id}_{mm_yyyy}"

    def _pdf_name(self) -> str:
        mm_yyyy     = self._gen_date.strftime("%m_%Y")
        lastname    = self.personal["lastname"].replace(" ", "_")
        firstname   = self.personal["firstname"].replace(" ", "_").replace("-", "_")
        jobtitle   = self.job.get("job_title", "").replace(" ", "_").replace("-", "_")
        offer_raw   = self.job.get("company_name") or self.job.get("id", "offre")
        offer_name  = re.sub(r"[^a-zA-Z0-9À-ÿ]+", "_", jobtitle).strip("_")
        return f"{lastname}_{firstname}_{offer_raw}_{offer_name}_{mm_yyyy}.pdf"

    # ------------------------------------------------------------------
    # Section renderers — each returns a LaTeX string
    # ------------------------------------------------------------------

    def _section_photo(self) -> str:
        return (
            r"\null\hfill" "\n"
            r"\includegraphics[width=0.60\textwidth]{pictures/photo_cv.jpg}" "\n"
            r"\hfill\null" "\n"
            r"\vspace*{0.3ex}" "\n"
        )

    def _section_disponibilite(self) -> str:
        p = self.personal
        dispo = p.get("disponibilite", "").strip()
        if not dispo:
            return ""
        return (
            r"\headleft{" + self._label("availability") + r"}" "\n"
            r"\small " + self._escape(dispo) + "\n"
            r"\normalsize" "\n"
        )

    def _section_informations(self) -> str:
        p = self.personal
        return (
            r"\headleft{" + self._label("contact") + r"}" "\n"
            r"\small" "\n"
            r"\textbf{" + self._label("email") + r":}\ \href{mailto:" + p["mail"] + r"}{" + self._escape(p["mail"]) + r"} \\[0.5ex]" "\n"
            r"\textbf{" + self._label("phone") + r":}\ " + self._escape(p["phone"]) + r" \\[0.5ex]" "\n"
            r"\textbf{" + self._label("linkedin") + r":}\ \href{https://linkedin.com/in/" + p["linkedin"] + r"}{"
            + self._escape(p["linkedin"]) + r"} \\[0.5ex]" "\n"
            r"\textbf{" + self._label("github") + r":}\ \href{https://github.com/" + p["github"] + r"}{"
            + self._escape(p["github"]) + r"} \\[0.5ex]" "\n"
            r"\textbf{" + self._label("location") + r":}\ " + self._escape(p["address"]) + "\n"
            r"\normalsize" "\n"
        )

    def _section_intitule_poste(self) -> str:
        """Affiche l'intitulé du poste visé.

        Logique de sélection (contrôlée par self._target_title_index) :

        - None (défaut) → mode auto :
            • job.job_title renseigné  → titre de l'offre
            • job.job_title absent     → cv_base.target_titles[0] (candidature spontanée)
        - int n → force candidature spontanée → code 1-based
            1 = Market Risk Analyst
            2 = Trading Analyst
            3 = Data Analyst
            …
        """
        idx = self._target_title_index
        if idx is not None:
            # Explicit index → always pick from cv_base.target_titles (1-based).
            cv_targets = self._normalize_lines((self.cv.get("target_titles") or "").replace(";", "\n"))
            normalized_idx = idx - 1
            title = cv_targets[normalized_idx] if 0 <= normalized_idx < len(cv_targets) else (cv_targets[0] if cv_targets else "")
        else:
            # Auto: use offer job_title if set, else first cv_base.target_titles entry.
            title = (self.job.get("job_title") or "").strip()
            if not title:
                cv_targets = self._normalize_lines((self.cv.get("target_titles") or "").replace(";", "\n"))
                title = cv_targets[0] if cv_targets else ""

        # Les titres spontanés sont stockés avec un préfixe numérique "01 ",
        # mais ce code ne fait pas apparaître sur le CV final.
        title = re.sub(r"^\d{2}\s+", "", title).strip()

        if not title:
            return ""
        return (
            r"\headleft{" + self._label("target_position") + r"}" "\n"
            r"\begin{center}" "\n"
            r"\vspace*{0.3ex}" "\n"
            r"{\bfseries\color{white}" + self._escape(title) + r"}\\[0.5pt]" "\n"
            r"\normalsize" "\n"
            r"\end{center}" "\n"
        )

    def _section_atouts(self) -> str:
        skills_text = self.cv.get("skills", "")
        lines = [l.strip().lstrip("•").strip() for l in skills_text.splitlines() if l.strip()]
        # For each of the first 3 lines, keep only the first 2 comma-separated parts
        snippets = []
        for line in lines:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            snippet = ", ".join(parts[:2]) # Keep up to 2 parts
            snippets.append(self._escape(snippet))
        content = r" \\[0.5ex]" "\n".join(snippets) if snippets else "~"
        return (
            r"\headleft{" + self._label("strengths") + r"}" "\n"
            r"\small " + content + "\n"
            r"\normalsize" "\n"
        )

    def _section_langues(self) -> str:
        langs = self._escape(self.cv.get("languages", ""))
        lines = [l.strip() for l in langs.replace(";", "\n").splitlines() if l.strip()]
        content = r" \\[0.4ex]" "\n".join(lines) if lines else "~"
        return r"\headleft{" + self._label("languages") + r"}" "\n" + content + "\n"

    def _section_centre_interet(self) -> str:
        interests = self.cv.get("interests", "")
        # Split on comma, strip bullets and whitespace
        parts = [p.strip().lstrip("•").strip() for p in interests.split(",") if p.strip()]
        line1 = ", ".join(parts[:2]) if len(parts) >= 1 else ""
        line2 = ", ".join(parts[2:4]) if len(parts) >= 3 else ""
        content = self._escape(line1)
        if line2:
            content += r"," r" \\[0.4ex]" "\n" + self._escape(line2)
        return (
            r"\headleft{" + self._label("interests") + r"}" "\n"
            r"\small " + content + "\n"
            r"\normalsize" "\n"
        )

    def _section_header(self) -> str:
        name    = self._escape(self.personal["name"])
        summary = self.cv.get("summary", "")
        lines   = [l.strip().lstrip("•").strip() for l in summary.splitlines() if l.strip()]
        summary_tex = " ".join(lines[:2]) if lines else ""
        return (
            r"\begin{center}" "\n"
            r"{\Large\bfseries\color{white}" + name + r"}\\[2pt]" "\n"
            r"\vspace*{0.3ex}" "\n"
            r"{\small\color{white}\jobtype}" "\n"
            r"\end{center}" "\n"
        )

    def _section_type_recherche(self) -> str:
        company = self._escape(self.job.get("company_name", ""))
        city    = self._escape(self.job.get("city", ""))
        country = self._escape(self.job.get("country", ""))
        loc     = ", ".join(filter(None, [city, country]))
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("search_type") + r"}}}" "\n"
            r"\textbf{\jobtype}" + (f" --- {company}" if company else "")
            + (f" ({loc})" if loc else "") + "\n"
        )

    # ----------------------------------------------------------------
    # Skills/competences sections : Not used
    # ----------------------------------------------------------------
    def _section_competences(self) -> str:
        lines = self._pick_lines(
            self.section_lines.get("competences", []),
            self.max_competences,
            self.selected_competence_indices,
        )
        escaped_lines = [self._escape(line) for line in lines]
        items = "\n".join(r"\item " + l for l in escaped_lines) if escaped_lines else r"\item ~"
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("skills") + r"}}}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            r"\setlength{\itemsep}{1pt}" "\n"
            r"\setlength{\parsep}{0pt}" "\n"
            r"\setlength{\topsep}{0pt}" "\n"
            r"\setlength{\partopsep}{1pt}" "\n"
            r"\setlength{\leftmargini}{6mm}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
        )


    # ----------------------------------------------------------------
    # Technical skills section : Used
    # ----------------------------------------------------------------


    def _competences_techniques_to_block(self, text: str, max_items: int = 0) -> str:
        """Render serialized competences techniques as simple blocks.

        Expected format per line:
        'field : description'

        Output:
        Line 1: field1 : description1
        Line 2: field2 : description2
        """
        if not text:
            return "~"

        blocks: List[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Remove bullet if present
            if line.startswith("•"):
                line = line[1:].strip()

            # Parse line
            parts = line.split(":")
            if len(parts) >= 2:
                field, desc = [p.strip() for p in parts[:2]]
            else:
                # fallback propre si format incorrect
                field = desc = ""

            # Build LaTeX strings (strings, pas listes)
            header = f"{field} : "
            subline = f"{desc}"

            # Escape
            escaped_header = self._escape(header)
            escaped_subline = self._escape(subline)


            # Build LaTeX block
            latex_lines = [
                r"\noindent " + escaped_header + r"\\" + "\n"
                + r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + escaped_subline
                + r"}" + "\n" + r"\par"
            ]

            block = "\n".join(latex_lines) + "\n\\par"
            blocks.append(block)

        if max_items > 0:
            blocks = blocks[:max_items]

        return "\n\\vspace{0.2ex}\n".join(blocks) if blocks else "~"

    def _section_competences_techniques(self) -> str:
        text = self._filter_text(self.cv.get("technical", ""), self.selected_competence_technique_indices, self.max_competences_techniques)
        blocks = self._competences_techniques_to_block(text, max_items=0)
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("technical_skills") + r"}}}" "\n"
            r"{\footnotesize" "\n"
            + blocks + "\n"
            r"}" "\n"
        )

    # ----------------------------------------------------------------
    # Experience formatter
    # ----------------------------------------------------------------

    def _experience_to_blocks(self, text: str, max_items: int = 0) -> str:
        """
            Render serialized experience as simple blocks.
            Expected format per line:
            'role | realisation | company | location | period | description'
            Output:
            Line 1: period : realisation company (location)
            Line 2: description, indented with a fixed left margin
        """
        if not text:
            return "~"
        blocks: List[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            # Remove bullet if present
            if line.startswith("•"):
                line = line[1:].strip()
            # Parse line
            parts = line.split("|")
            if len(parts) >= 7:
                role, realisation, company, loc, period, desc, mots_cles  = [p.strip() for p in parts[:7]]
            else:
                # fallback propre si format incorrect
                role = realisation = company = loc = period = desc = mots_cles = ""

            # Escape 
            clean_mots_cles = self.normalize_keywords(mots_cles)
            escaped_realisation = CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(realisation.strip()))
            
            # Protection contre les coupures de mots dans desc
            clean_desc = self.clean_ocr_text(desc)
            escaped_desc =  CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(clean_desc.strip()))
            escaped_mots_cles =  CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(clean_mots_cles.strip()))

            escaped_header = f"{period} : {escaped_realisation} {company} ({loc})"
            
            escaped_subline = f"{escaped_desc}"
            escaped_sub_subline = f"{escaped_mots_cles}"
            # Build LaTeX block
            latex_lines = [
                r"\noindent " + escaped_header + r"\\",
                r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + (escaped_subline or "") + r"}\\",
                r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + self._label("keywords") + " : " + (escaped_sub_subline or "") + r"}",
                r"\vspace{0.1em}"
            ]
            block = "\n".join(latex_lines) + "\n\\par"
            blocks.append(block)

        if max_items > 0:
            blocks = blocks[:max_items]
        return "\n\\vspace{0.2ex}\n".join(blocks) if blocks else "~"

    def _section_experiences(self) -> str:
        text = self._filter_text(self.cv.get("experience", ""), self.selected_experience_indices, self.max_experiences)
        blocks = self._experience_to_blocks(text, max_items=0)
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("experience") + r"}}}" "\n"
            r"{\footnotesize" "\n"
            + blocks + "\n"
            r"}" "\n"
        )

    def _education_to_blocks(self, text: str, max_items: int = 0) -> str:
        """Render serialized education as simple blocks.

        Expected format per line:
        'degree | field | school | location | period | description'

        Output:
        Line 1: period + degree
        Line 2: field at school (location)
        Line 3: description
        """
        if not text:
            return "~"

        blocks: List[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Remove bullet if present
            if line.startswith("•"):
                line = line[1:].strip()

            # Parse line
            parts = line.split("|")
            if len(parts) >= 6:
                degree, field, school, location, period, desc = [p.strip() for p in parts[:6]]
            else:
                # fallback propre si format incorrect
                degree = field = school = location = period = desc = ""

            # Build LaTeX strings (strings, pas listes)
            escaped_degree = CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(degree.strip()))
            
            header = f"{period} {escaped_degree}"
            subline = f"{field} {school} ({location})"

            # Escape
            escaped_header = self._escape(header)
            escaped_subline = self._escape(subline)

            # protection contre les coupures des mots dans desc
            clean_desc = self.clean_ocr_text(desc)
            escaped_desc = self._escape(clean_desc)

            # Build LaTeX block
            latex_lines = [
                r"\noindent " + escaped_header + r"\\" + "\n"
                + r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + escaped_subline
                + r"}" + "\n" + r"\par",
                r"\vspace{0.5em}"
            ]
            full_latex_lines = []
            if escaped_desc:
                full_latex_lines.append(rf"\noindent {escaped_desc}")

            block = "\n".join(latex_lines) + "\n\\par"
            blocks.append(block)

        if max_items > 0:
            blocks = blocks[:max_items]

        return "\n\\vspace{0.2ex}\n".join(blocks) if blocks else "~"
    

    def _section_formations(self) -> str:
        blocks = self._education_to_blocks(self.cv.get("education", ""), max_items=4)
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("education") + r"}}}" "\n"
            r"{\footnotesize" "\n"
            + blocks + "\n"
            r"}" "\n"
        )

    def _section_certifications(self) -> str:
        text = self._escape(self.cv.get("certifications", ""))
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("certifications") + r"}}}" "\n"
            r"{\footnotesize" "\n"
            + text + "\n"
            r"}" "\n"
        )


    def _project_to_blocks(self, text: str, max_items: int = 0) -> str:
        """
        Render project lines as two-line blocks, similar to experiences:
          line 1: project header (or full line if no description split)
          line 2: description, indented with a fixed left margin
        """
        if not text:
                return "~"
        blocks: List[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            # Remove bullet if present
            if line.startswith("•"):
                line = line[1:].strip()
            # Parse line
            parts = line.split("|")
            if len(parts) >= 5:
                ref, title, mots_cles, period, desc = [p.strip() for p in parts[:5]]
            else:
                # fallback propre si format incorrect
                ref = title = mots_cles = period = desc = ""
            if not self.is_not_empty(ref, title, desc):
                continue
            # Escape 
            clean_mots_cles = self.normalize_keywords(mots_cles)

            escaped_title = CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(title.strip()))
            
            # Protection contre les coupures de mots dans desc
            clean_desc = self.clean_ocr_text(desc)
            escaped_desc =  CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(clean_desc.strip()))
            escaped_mots_cles =  CVLatexGeneratorBase._md_inline(CVLatexGeneratorBase._escape(clean_mots_cles.strip()))
            
            escaped_header = f"{escaped_title} : "
            escaped_subline = f"{escaped_desc}"
            escaped_sub_subline = f"{escaped_mots_cles}"

            # Build LaTeX block
            latex_lines = [
                r"\noindent " + escaped_header + r"\\",
                r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + (escaped_subline or "") + r"}\\",
                r"\noindent\hspace*{10mm}\parbox[t]{\dimexpr\linewidth-10mm\relax}{"
                + self._label("keywords") + " : " + (escaped_sub_subline or "") + r"}",
                r"\vspace{0.1em}"
            ]
            block = "\n".join(latex_lines) + "\n\\par"
            blocks.append(block)

        if max_items > 0:
            blocks = blocks[:max_items]
        return "\n\\vspace{0.2ex}\n".join(blocks) if blocks else "~"

    def _section_projets(self) -> str:
        text = self._filter_text(self.cv.get("projects", ""), self.selected_project_indices, self.max_projects)
        blocks = self._project_to_blocks(text, max_items=0)
        
        return (
            r"\headright{\Large\bfseries{\MakeUppercase{" + self._label("projects") + r"}}}" "\n"
            r"{\footnotesize" "\n"
            + blocks + "\n"
            r"}" "\n"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_sections(self) -> Dict[str, str]:
        """Return dict of section filename → LaTeX content."""
        return {
            "photo.tex":                  self._section_photo(),
            "disponibilite.tex":          self._section_disponibilite(),
            "informations.tex":           self._section_informations(),
            "intitule_poste.tex":         self._section_intitule_poste(),
            "atouts.tex":                 self._section_atouts(),
            "langues.tex":                self._section_langues(),
            "centre_interet.tex":         self._section_centre_interet(),
            "header.tex":                 self._section_header(),
            "type_recherche.tex":         self._section_type_recherche(),
            "competences.tex":            self._section_competences(),
            "competences_techniques.tex": self._section_competences_techniques(),
            "experiences.tex":            self._section_experiences(),
            "formations.tex":             self._section_formations(),
            "certifications.tex":         self._section_certifications(),
            "projets.tex":                self._section_projets(),
        }

    def write_tex_bundle(self, build_dir: Path) -> Path:
        """
        Write main_fr.tex (with personal info substituted) + all sections
        into build_dir. Returns path to the main .tex file.
        """
        build_dir = Path(build_dir)
        sections_dir = build_dir / "sections"
        sections_dir.mkdir(parents=True, exist_ok=True)

        # Read template
        template_path = _TEMPLATE_DIR / "main_fr.tex"
        tex = template_path.read_text(encoding="utf-8")
        tex = tex.replace(r"\usepackage[french]{babel}", rf"\usepackage[{self._babel_package_language()}]{{babel}}")

        # Substitute personal info placeholders
        p = self.personal
        substitutions = {
            "<<CVNAME>>":       self._escape(p["name"]),
            "<<CVADDRESS>>":    self._escape(p["address"]),
            "<<CVMAIL>>":       p["mail"],
            "<<CVPHONE>>":      self._escape(p["phone"]),
            "<<CVLINKEDIN>>":   p["linkedin"],
            "<<CVGITHUB>>":     p["github"],
            "<<JOBTYPE>>":      self._escape(p["jobtype"]),
            "<<PRESENTATION>>": self._escape(self.cv.get("summary", "")[:200]),
        }
        for placeholder, value in substitutions.items():
            tex = tex.replace(placeholder, value)

        tex_path = build_dir / "main_fr.tex"
        tex_path.write_text(tex, encoding="utf-8")

        # Write section files
        for filename, content in self.render_sections().items():
            (sections_dir / filename).write_text(content, encoding="utf-8")

        # Copy photo if it exists in the pictures dir
        photo_src = _TEMPLATE_DIR.parent / "pictures" / "photo_cv.jpg"
        if photo_src.exists():
            pictures_dir = build_dir / "pictures"
            pictures_dir.mkdir(exist_ok=True)
            shutil.copy2(photo_src, pictures_dir / "photo_cv.jpg")

        return tex_path

    def compile_pdf(self, build_dir: Path) -> Path:
        """
        Run pdflatex twice in build_dir to produce main_fr.pdf.
        Returns the path to the generated PDF.
        Raises RuntimeError if pdflatex fails.
        """
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main_fr.tex"]
        for _ in range(2):  # two passes for lastpage / refs
            result = subprocess.run(
                cmd,
                cwd=build_dir,
                capture_output=True,
            )
            if result.returncode != 0:
                stdout = result.stdout.decode("utf-8", errors="replace")
                stderr = result.stderr.decode("utf-8", errors="replace")
                log_snippet = stdout[-2000:] + stderr[-500:]
                raise RuntimeError(f"pdflatex failed:\n{log_snippet}")

        return build_dir / "main_fr.pdf"

    def generate(self) -> Tuple[Path, Path]:
        """
        Full pipeline:
          1. Write .tex bundle to a temp build dir
          2. Compile to PDF
          3. Copy outputs to self.output_dir:
               - archiv_{job_id}_{cv_id}_{mm}_{yyyy}.tex
               - {lastname}_{firstname}_{offer_raw}_{offer_name}_{mm_yyyy}.pdf
          4. Clean up build dir

        Returns (tex_dest, pdf_dest).
        """
        stem     = self._output_stem()
        pdf_name = self._pdf_name()

        with tempfile.TemporaryDirectory(prefix="cvlatex_") as tmp:
            build_dir = Path(tmp)
            self.write_tex_bundle(build_dir)

            logger.info("Compiling CV LaTeX for %s …", stem)
            pdf_src = self.compile_pdf(build_dir)

            tex_dest = self.output_dir / f"{stem}.tex"
            pdf_dest = self.output_dir / pdf_name

            shutil.copy2(build_dir / "main_fr.tex", tex_dest)
            shutil.copy2(pdf_src, pdf_dest)

        logger.info("CV generated: %s | %s", tex_dest.name, pdf_dest.name)
        return tex_dest, pdf_dest


class CVLatexGeneratorFR(CVLatexGeneratorBase):
    """French two-column CV PDF generator."""

    _LANGUAGE = "fr"


class CVLatexGeneratorEN(CVLatexGeneratorBase):
    """English two-column CV PDF generator."""

    _LANGUAGE = "en"


