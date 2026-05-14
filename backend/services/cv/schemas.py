# *-- UTF-8 --*
"""
Schémas de validation des requêtes et réponses pour le service CV.
Chaque schéma expose :
    - validate(data: dict) → None  (lève ValueError si invalide)
    - REQUIRED / OPTIONAL         (champs documentés)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_TABLES = {"cv_base", "jobs", "cv_applications", "applications"}
_VALID_ACTIONS = {"add", "get", "update", "delete", "list", "summary", "ingest"}


def _require(data: dict, *fields: str) -> None:
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise ValueError(f"Champ(s) requis manquant(s) : {missing}")


# ---------------------------------------------------------------------------
# DB pipeline — schémas de requête
# ---------------------------------------------------------------------------

class DBSummarySchema:
    """GET /cv/db/summary  — aucun corps."""


class DBListSchema:
    """GET /cv/db/<table>?language=fr&…"""
    OPTIONAL = ["language"]

    @staticmethod
    def validate(params: dict) -> None:
        table = params.get("table", "")
        if table not in _VALID_TABLES:
            raise ValueError(f"Table inconnue : '{table}'. Valeurs valides : {sorted(_VALID_TABLES)}")


class DBGetSchema:
    """GET /cv/db/<table>/<id>"""

    @staticmethod
    def validate(params: dict) -> None:
        _require(params, "table", "record_id")
        if params["table"] not in _VALID_TABLES:
            raise ValueError(f"Table inconnue : '{params['table']}'")


class DBAddCVBaseSchema:
    """
    POST /cv/db/cv_base
    Corps optionnel : { "source": "cv_base_fr.json" }
    Si absent → ingère tous les fichiers de docs/cv_base/.
    """
    OPTIONAL = ["source"]

    @staticmethod
    def validate(data: dict) -> None:
        # source est optionnel mais doit être un nom de fichier .json si fourni
        src = data.get("source")
        if src and not src.endswith(".json"):
            raise ValueError("'source' doit être un nom de fichier .json (ex: cv_base_fr.json)")


class DBAddSchema:
    """
    POST /cv/db/<table>  (jobs, cv_applications, applications)
    Corps : champs de la table.
    """
    REQUIRED_BY_TABLE: Dict[str, List[str]] = {
        "jobs":            ["id", "language", "country"],
        "cv_applications": ["id", "cv_base_id", "job_id"],
        "applications":    ["id", "cv_application_id"],
    }

    @staticmethod
    def validate(data: dict) -> None:
        table = data.get("table", "")
        required = DBAddSchema.REQUIRED_BY_TABLE.get(table, [])
        _require(data.get("body", {}), *required)


class DBUpdateSchema:
    """PUT /cv/db/<table>/<id>  — corps : champs à modifier."""

    @staticmethod
    def validate(data: dict) -> None:
        _require(data, "table", "record_id")
        if not data.get("body"):
            raise ValueError("Le corps de la mise à jour ne peut pas être vide.")
        if data["table"] not in _VALID_TABLES:
            raise ValueError(f"Table inconnue : '{data['table']}'")


class DBDeleteSchema:
    """DELETE /cv/db/<table>/<id>"""

    @staticmethod
    def validate(data: dict) -> None:
        _require(data, "table", "record_id")
        if data["table"] not in _VALID_TABLES:
            raise ValueError(f"Table inconnue : '{data['table']}'")


# ---------------------------------------------------------------------------
# CV generation — schémas de requête
# ---------------------------------------------------------------------------

class CVGenerateFRSchema:
    """
    POST /cv/generate/fr
    Corps requis :
        cv_base_id         : str   — ex: "cv_base_in_all_fr"
        job_id             : str   — ex: "offer-711607447"
    Corps optionnel :
        target_title_index : int   — 0/1/2/3/… ; 0 ou absent = auto
        db_path            : str   — chemin custom vers jobcv.db
        max_projects       : int   — 0 = tous les projets retenus
        max_experiences    : int   — 0 = toutes les expériences retenues
        selected_project_indices : list[int] — indices 0-based, vide/absent = tous
        selected_experience_indices : list[int] — indices 0-based, vide/absent = toutes
    """
    REQUIRED = ["cv_base_id", "job_id"]
    OPTIONAL = [
        "target_title_index",
        "db_path",
        "max_projects",
        "max_experiences",
        "selected_project_indices",
        "selected_experience_indices",
    ]

    @staticmethod
    def validate(data: dict) -> None:
        _require(data, "cv_base_id", "job_id")
        tti = data.get("target_title_index")
        if tti is not None and not isinstance(tti, int):
            raise ValueError("'target_title_index' doit être un entier.")
        if isinstance(tti, int) and tti < 0:
            raise ValueError("'target_title_index' doit être un entier >= 0.")

        for field in ("max_projects", "max_experiences"):
            value = data.get(field)
            if value is not None and not isinstance(value, int):
                raise ValueError(f"'{field}' doit être un entier.")
            if isinstance(value, int) and value < 0:
                raise ValueError(f"'{field}' doit être un entier >= 0.")

        for field in ("selected_project_indices", "selected_experience_indices"):
            value = data.get(field)
            if value is None:
                continue
            if not isinstance(value, list):
                raise ValueError(f"'{field}' doit être une liste d'entiers.")
            if any(not isinstance(item, int) for item in value):
                raise ValueError(f"'{field}' doit contenir uniquement des entiers.")
            if any(item < 0 for item in value):
                raise ValueError(f"'{field}' doit contenir uniquement des entiers >= 0.")
        


class CVGenerateENSchema(CVGenerateFRSchema):
    """
    POST /cv/generate/en
    Même schéma que FR, avec un cv_base en anglais.
    """


# ---------------------------------------------------------------------------
# Réponses standard
# ---------------------------------------------------------------------------

def ok(data: Any, message: str = "OK") -> Dict[str, Any]:
    return {"status": "ok", "message": message, "data": data}


def error(message: str, code: int = 400) -> Dict[str, Any]:
    return {"status": "error", "message": message, "code": code}
