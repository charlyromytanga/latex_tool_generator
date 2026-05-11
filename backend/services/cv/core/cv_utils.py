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
            "experience", "education", "certifications", "projects",
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

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row else None

    def _upsert(self, table: str, data: Dict[str, Any]) -> None:
        """INSERT OR REPLACE into table with the given data dict."""
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
        """UPDATE table SET field=value, ... WHERE id=record_id. Returns rowcount."""
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
        with self._connect() as conn:
            cur = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
            return self._row_to_dict(cur.fetchone())

    def _delete(self, table: str, record_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            return cur.rowcount

    def _list(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
        result: Dict[str, int] = {}
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

_TEMPLATE_DIR = Path(
    _os.environ.get(
        "CV_TEMPLATE_DIR",
        str(Path(__file__).resolve().parents[4] / "shared" / "service_cv_latex" / "templates" / "_col_gauche"),
    )
)
_OUTPUT_DIR = Path(
    _os.environ.get(
        "CV_OUTPUT_DIR",
        str(Path(__file__).resolve().parents[4] / "shared" / "output" / "FR"),
    )
)


class CVLatexGeneratorFR:
    """
    Generates a French two-column CV PDF from CVBase + Jobs data.

    Usage (standalone, outside Flask):
        gen = CVLatexGeneratorFR.from_db(
            db_path="/app/db/jobcv.db",
            cv_base_id="cv_base_in_all_fr",
            job_id="<job_uuid>",
        )
        tex_path, pdf_path = gen.generate()

    Usage (within Flask, passing model instances):
        cv_dict  = {col: getattr(cv_base_obj, col) for col in CVBase.__table__.columns.keys()}
        job_dict = {col: getattr(job_obj, col) for col in Jobs.__table__.columns.keys()}
        gen = CVLatexGeneratorFR(cv_dict, job_dict)
        tex_path, pdf_path = gen.generate()
    """

    _DEFAULT_PERSONAL: Dict[str, str] = {
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

    def __init__(
        self,
        cv_base: Dict[str, Any],
        job: Dict[str, Any],
        personal: Optional[Dict[str, str]] = None,
        output_dir: Optional[Path] = None,
        target_title_index: Optional[int] = None,
    ):
        self.cv = cv_base
        self.job = job
        self.personal = {**self._DEFAULT_PERSONAL, **(personal or {})}
        self.output_dir = Path(output_dir) if output_dir else _OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._gen_date = datetime.now()
        # None  → auto : job_title si disponible dans l'offre, sinon target_titles[0]
        # int   → candidature spontanée : force target_titles[n]
        self._target_title_index = target_title_index

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
    ) -> "CVLatexGeneratorFR":
        """Load CVBase + Jobs rows from SQLite and return a configured instance.

        Args:
            db_path: Path to the SQLite DB.
            cv_base_id: ID of the cv_base row.
            job_id: ID of the jobs row (must exist, even for spontaneous applications —
                    use a placeholder job row with no job_title set).
            target_title_index: If None (default), use job.job_title when set, else
                fallback to cv_base.target_titles[0].
                If an int, force spontaneous mode and pick target_titles[n].
                  0 → Market Risk Analyst
                  1 → Trading Analyst
                  2 → Data Analyst
        """
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

        return cls(
            cv_base=dict(row_cv),
            job=dict(row_job),
            personal=personal,
            output_dir=output_dir,
            target_title_index=target_title_index,
        )

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

    def _output_stem(self) -> str:
        mm_yyyy = self._gen_date.strftime("%m_%Y")
        cv_id   = self.cv.get("id", "cv")
        job_id  = self.job.get("id", "job")
        return f"archiv_{job_id}_{cv_id}_{mm_yyyy}"

    def _pdf_name(self) -> str:
        mm_yyyy     = self._gen_date.strftime("%m_%Y")
        lastname    = self.personal["lastname"].replace(" ", "_")
        firstname   = self.personal["firstname"].replace(" ", "_").replace("-", "_")
        offer_raw   = self.job.get("company_name") or self.job.get("id", "offre")
        offer_name  = re.sub(r"[^a-zA-Z0-9À-ÿ]+", "_", offer_raw).strip("_")
        return f"{lastname}_{firstname}_{offer_name}_{mm_yyyy}.pdf"

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
            r"\headleft{Disponibilit\'{e}}" "\n"
            r"\small " + self._escape(dispo) + "\n"
            r"\normalsize" "\n"
        )

    def _section_informations(self) -> str:
        p = self.personal
        return (
            r"\headleft{Contact}" "\n"
            r"\small" "\n"
            r"\faEnvelope\ \href{mailto:" + p["mail"] + r"}{" + self._escape(p["mail"]) + r"} \\[0.5ex]" "\n"
            r"\faMobile*\ " + self._escape(p["phone"]) + r" \\[0.5ex]" "\n"
            r"\faLinkedin\ \href{https://linkedin.com/in/" + p["linkedin"] + r"}{"
            + self._escape(p["linkedin"]) + r"} \\[0.5ex]" "\n"
            r"\faGithub\ \href{https://github.com/" + p["github"] + r"}{"
            + self._escape(p["github"]) + r"} \\[0.5ex]" "\n"
            r"\faMapMarker\ " + self._escape(p["address"]) + "\n"
            r"\normalsize" "\n"
        )

    def _section_intitule_poste(self) -> str:
        """Affiche l'intitulé du poste visé.

        Logique de sélection (contrôlée par self._target_title_index) :

        - None (défaut) → mode auto :
            • job.job_title renseigné  → titre de l'offre
            • job.job_title absent     → cv_base.target_titles[0] (candidature spontanée)
        - int n → force candidature spontanée → cv_base.target_titles[n]
            0 = Market Risk Analyst
            1 = Trading Analyst
            2 = Data Analyst
            …
        """
        raw_targets = self.cv.get("target_titles") or ""
        targets = [t.strip() for t in raw_targets.split(";") if t.strip()]

        idx = self._target_title_index
        if idx is not None:
            # Candidature spontanée forcée
            title = targets[idx] if idx < len(targets) else (targets[0] if targets else "")
        else:
            # Auto : offre si dispo, sinon premier titre spontané
            title = (self.job.get("job_title") or "").strip()
            if not title:
                title = targets[0] if targets else ""

        if not title:
            return ""
        return (
            r"\headleft{Poste vis\'{e}}" "\n"
            r"\begin{center}" "\n"
            r"\vspace*{0.3ex}" "\n"
            r"{\Large\bfseries\color{white}" + self._escape(title) + r"}\\[2pt]" "\n"
            r"\normalsize" "\n"
            r"\end{center}" "\n"
        )

    def _section_atouts(self) -> str:
        skills_text = self.cv.get("skills", "")
        lines = [l.strip().lstrip("•").strip() for l in skills_text.splitlines() if l.strip()]
        # For each of the first 3 lines, keep only the first 2 comma-separated parts
        snippets = []
        for line in lines[:3]:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            snippet = ", ".join(parts[:2])
            snippets.append(self._escape(snippet))
        content = r" \\[0.5ex]" "\n".join(snippets) if snippets else "~"
        return (
            r"\headleft{Atouts}" "\n"
            r"\small " + content + "\n"
            r"\normalsize" "\n"
        )

    def _section_langues(self) -> str:
        langs = self._escape(self.cv.get("languages", ""))
        lines = [l.strip() for l in langs.replace(";", "\n").splitlines() if l.strip()]
        content = r" \\[0.4ex]" "\n".join(lines) if lines else "~"
        return r"\headleft{Langues}" "\n" + content + "\n"

    def _section_centre_interet(self) -> str:
        interests = self.cv.get("interests", "")
        # Split on comma, strip bullets and whitespace
        parts = [p.strip().lstrip("•").strip() for p in interests.split(",") if p.strip()]
        line1 = ", ".join(parts[:2]) if len(parts) >= 1 else ""
        line2 = ", ".join(parts[2:4]) if len(parts) >= 3 else ""
        content = self._escape(line1)
        if line2:
            content += r" \\[0.4ex]" "\n" + self._escape(line2)
        return (
            r"\headleft{Centres d'int\'{e}r\^{e}t}" "\n"
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
            r"\headright{Type de recherche}" "\n"
            r"\textbf{\jobtype}" + (f" --- {company}" if company else "")
            + (f" ({loc})" if loc else "") + "\n"
        )

    def _section_competences(self) -> str:
        # Show first half only (soft skills)
        skills_text = self.cv.get("skills", "")
        lines = [l.strip().lstrip("•").strip() for l in skills_text.splitlines() if l.strip()]
        mid = max(1, len(lines) // 2)
        items = "\n".join(r"\item " + l for l in lines[:mid][:2]) if lines else r"\item ~"
        return (
            r"\headright{Comp\'{e}tences}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
        )

    def _section_competences_techniques(self) -> str:
        # Second half of skills — technical
        skills_text = self.cv.get("skills", "")
        lines = [l.strip().lstrip("•").strip() for l in skills_text.splitlines() if l.strip()]
        mid = max(1, len(lines) // 2)
        tech_lines = lines[mid:] if mid > 0 else lines
        items = "\n".join(r"\item " + l for l in tech_lines[:3]) if tech_lines else r"\item ~"
        return (
            r"\headright{Connaissances techniques}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
        )

    def _section_experiences(self) -> str:
        items = self._bullets_to_items(self.cv.get("experience", ""), max_items=8, truncate=True)
        return (
            r"\headright{Exp\'{e}riences professionnelles}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
        )

    def _section_formations(self) -> str:
        items = self._bullets_to_items(self.cv.get("education", ""), max_items=2, truncate=True)
        return (
            r"\headright{Formations}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
        )

    def _section_certifications(self) -> str:
        text = self._escape(self.cv.get("certifications", ""))
        return r"\headright{Certifications}" "\n" + text + "\n"

    def _section_projets(self) -> str:
        items = self._bullets_to_items(self.cv.get("projects", ""), max_items=10, truncate=True)
        return (
            r"\headright{Projets}" "\n"
            r"{\footnotesize\begin{itemize}" "\n"
            + items + "\n"
            r"\end{itemize}}" "\n"
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
                text=True,
            )
            if result.returncode != 0:
                log_snippet = result.stdout[-2000:] + result.stderr[-500:]
                raise RuntimeError(f"pdflatex failed:\n{log_snippet}")

        return build_dir / "main_fr.pdf"

    def generate(self) -> Tuple[Path, Path]:
        """
        Full pipeline:
          1. Write .tex bundle to a temp build dir
          2. Compile to PDF
          3. Copy outputs to self.output_dir:
               - archiv_{job_id}_{cv_id}_{mm}_{yyyy}.tex
               - {LASTNAME}_{Firstname}_{Company}_{mm}_{yyyy}.pdf
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


