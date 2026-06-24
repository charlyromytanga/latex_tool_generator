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
    from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications
except ImportError:
    db = CVBase = Jobs = CVApplications = Applications = None # type:   ignore

def _get_falsk_db():
    """ Returns the Flask SQLAlchemy db object if inside de Flask app context, otherwise returns None. """
    if db is None or CVBase is None or Jobs is None or CVApplications is None or Applications is None:
        return None
    try:
        from flask import current_app
        current_app._get_current_object()
        return db
    except (RuntimeError, ImportError):
        return None

_MODEL_MAP: Dict[str, Any] = {}

def _model_map() -> Dict[str, Any] : 
    if CVBase is not None and not _MODEL_MAP:
        _MODEL_MAP.update({
            "cv_base": CVBase,
            "jobs": Jobs,
            "cv_applications": CVApplications,
            "applications": Applications
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
# LM LaTeX Generator:  FR / EN
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
        "LM_TEMPLATE_DIR",
        str(_REPO_ROOT / "shared" / "service_lm_latex" / "templates" / "fr")
    )
)
_OUTPUT_DIR = Path(
    _os.environ.get(
        "LM_OUTPUT_DIR",
        str(_REPO_ROOT / "shared" / "output" / "FR")
    )
)
_OUTPUT_DIR_BY_LANGUAGE : Dict[str, Path] ={
    "fr" : _OUTPUT_DIR,
    "en" : Path(
        _os.environ.get(
            "LM_OUTPUT_DIR_EN",
            str(_REPO_ROOT / "shared" / "output" / "EN")
        )
    )
}
_TEMPLATE_DIR_BY_LANGUAGE : Dict[str, Path] = {
    "fr": _TEMPLATE_DIR,
    "en": Path(
        _os.environ.get(
            "LM_TEMPLATE_DIR_EN",
            str(_REPO_ROOT / "shared" / "service_lm_latex" / "templates" / "en")
        )
    )
}