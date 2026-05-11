# *-- UTF-8 --*
"""
Routes du service CV — blueprint Flask enregistré sous le préfixe /cv.

Endpoints :
    GET    /cv/db/summary                → résumé des tables
    GET    /cv/db/<table>                → liste des enregistrements
    GET    /cv/db/<table>/<id>           → récupère un enregistrement
    POST   /cv/db/cv_base                → ingère depuis docs/cv_base/ (ingesteur JSON)
    POST   /cv/db/<table>                → ajoute un enregistrement (jobs/cv_applications/applications)
    PUT    /cv/db/<table>/<id>           → met à jour un enregistrement
    DELETE /cv/db/<table>/<id>           → supprime un enregistrement
    POST   /cv/generate/fr               → génère le PDF LaTeX FR
"""

from __future__ import annotations

import logging
import os
import sys

from flask import Blueprint, jsonify, request, send_file

# Imports compatibles package ET exécution directe
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
try:
    from .core.cv_business import run_db_pipeline, run_cv_fr_pipeline, _DEFAULT_DB_PATH
except ImportError:
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    from backend.services.cv.core.cv_business import run_db_pipeline, run_cv_fr_pipeline, _DEFAULT_DB_PATH  # type: ignore

try:
    from .schemas import (
        DBAddCVBaseSchema, DBAddSchema, DBGetSchema, DBListSchema,
        DBUpdateSchema, DBDeleteSchema, CVGenerateFRSchema, ok, error,
    )
except ImportError:
    from backend.services.cv.schemas import (  # type: ignore
        DBAddCVBaseSchema, DBAddSchema, DBGetSchema, DBListSchema,
        DBUpdateSchema, DBDeleteSchema, CVGenerateFRSchema, ok, error,
    )

logger = logging.getLogger(__name__)

cv_blueprint = Blueprint("cv", __name__)

_DOCS_ROOT = os.path.join(_REPO_ROOT, "docs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_path() -> str:
    return request.args.get("db_path") or _DEFAULT_DB_PATH


def _source_path(table: str, filename: str | None) -> str | None:
    if not filename:
        return None
    return os.path.join(_DOCS_ROOT, table, filename)


_OUTPUT_BASE = os.environ.get("CV_OUTPUT_BASE", "/app/shared/output")


def _output_dir(lang: str = "FR") -> str:
    """Retourne le répertoire de sortie pour une langue donnée."""
    return os.path.join(_OUTPUT_BASE, lang.upper())


# ---------------------------------------------------------------------------
# CV output — serve generated PDF
# ---------------------------------------------------------------------------

@cv_blueprint.route("/output/<lang>/<path:filename>", methods=["GET"])
@cv_blueprint.route("/output/<path:filename>", methods=["GET"])
def serve_output(filename: str, lang: str = "FR"):
    """Sert un fichier généré (PDF ou TEX) depuis shared/output/{lang}/."""
    safe = os.path.basename(filename)
    full_path = os.path.join(_output_dir(lang), safe)
    if not os.path.isfile(full_path):
        return jsonify(error(f"Fichier introuvable : {safe}", 404)), 404
    return send_file(full_path, as_attachment=False,
                     download_name=safe,
                     mimetype="application/pdf" if safe.endswith(".pdf") else "text/plain")


@cv_blueprint.route("/check/<cv_base_id>/<job_id>", methods=["GET"])
def check_existing_pdf(cv_base_id: str, job_id: str):
    """
    Vérifie si un PDF a déjà été généré pour ce couple cv_base_id / job_id ce mois-ci.
    Détecte la présence du fichier .tex d'archive (archiv_{job_id}_{cv_base_id}_{mm_yyyy}.tex)
    puis retourne le premier .pdf trouvé dans le même dossier.
    Renvoie {"exists": true, "filename": "...", "lang": "FR"} ou {"exists": false}.
    """
    from datetime import datetime
    mm_yyyy = datetime.now().strftime("%m_%Y")
    tex_stem = f"archiv_{job_id}_{cv_base_id}_{mm_yyyy}"

    if not os.path.isdir(_OUTPUT_BASE):
        return jsonify(ok({"exists": False}, "Aucun PDF trouvé")), 200

    for lang_dir in os.listdir(_OUTPUT_BASE):
        dir_path = os.path.join(_OUTPUT_BASE, lang_dir)
        if not os.path.isdir(dir_path):
            continue
        files = os.listdir(dir_path)
        # Vérifier la présence du .tex d'archive pour ce job/cv/mois
        tex_found = any(f == f"{tex_stem}.tex" for f in files)
        if tex_found:
            # Retourner le premier PDF du dossier (il n'y en a qu'un par génération)
            pdfs = [f for f in files if f.endswith(".pdf")]
            if pdfs:
                return jsonify(ok({"exists": True, "filename": pdfs[0], "lang": lang_dir}, "PDF trouvé")), 200

    return jsonify(ok({"exists": False}, "Aucun PDF trouvé")), 200


# ---------------------------------------------------------------------------
# DB — summary
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/summary", methods=["GET"])
def db_summary():
    """Retourne le nombre d'enregistrements par table."""
    try:
        result = run_db_pipeline(table="", action="summary", record_id="", db_path=_db_path())
        return jsonify(ok(result, "Résumé des tables")), 200
    except Exception as exc:
        logger.exception("db_summary error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — list
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/<table>", methods=["GET"])
def db_list(table: str):
    """Liste les enregistrements d'une table. Filtres via query params (ex: ?language=fr)."""
    try:
        DBListSchema.validate({"table": table})
        filters = {k: v for k, v in request.args.items() if k != "db_path"}
        result = run_db_pipeline(table=table, action="list", record_id="",
                                 filters=filters or None, db_path=_db_path())
        return jsonify(ok(result or [])), 200
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_list error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — get
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/<table>/<record_id>", methods=["GET"])
def db_get(table: str, record_id: str):
    """Récupère un enregistrement par son id."""
    try:
        DBGetSchema.validate({"table": table, "record_id": record_id})
        result = run_db_pipeline(table=table, action="get", record_id=record_id, db_path=_db_path())
        if result is None:
            return jsonify(error(f"Enregistrement '{record_id}' introuvable dans '{table}'.", 404)), 404
        return jsonify(ok(result)), 200
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_get error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — add cv_base  (passe toujours par l'ingesteur JSON)
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/cv_base", methods=["POST"])
def db_add_cv_base():
    """
    Ingère cv_base depuis docs/cv_base/.
    Corps JSON optionnel : { "source": "cv_base_fr.json" }
    Absent → ingère tous les fichiers.
    """
    body = request.get_json(silent=True) or {}
    try:
        DBAddCVBaseSchema.validate(body)
        source = _source_path("cv_base", body.get("source"))
        result = run_db_pipeline(table="cv_base", action="add", record_id="",
                                 db_path=_db_path(), source_path=source)
        return jsonify(ok(result, "cv_base ingéré")), 201
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_add_cv_base error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — add (jobs, cv_applications, applications)
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/<table>", methods=["POST"])
def db_add(table: str):
    """Ajoute un enregistrement dans jobs, cv_applications ou applications."""
    body = request.get_json(silent=True) or {}
    try:
        if table == "cv_base":
            # Redirection vers le handler dédié
            return db_add_cv_base()
        DBAddSchema.validate({"table": table, "body": body})
        result = run_db_pipeline(table=table, action="add", record_id="",
                                 data=body, db_path=_db_path())
        return jsonify(ok(result, f"{table} ajouté")), 201
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_add error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — update
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/<table>/<record_id>", methods=["PUT"])
def db_update(table: str, record_id: str):
    """Met à jour un enregistrement existant."""
    body = request.get_json(silent=True) or {}
    try:
        DBUpdateSchema.validate({"table": table, "record_id": record_id, "body": body})
        result = run_db_pipeline(table=table, action="update", record_id=record_id,
                                 data=body, db_path=_db_path())
        return jsonify(ok(result, f"{table}/{record_id} mis à jour")), 200
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_update error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# DB — delete
# ---------------------------------------------------------------------------

@cv_blueprint.route("/db/<table>/<record_id>", methods=["DELETE"])
def db_delete(table: str, record_id: str):
    """Supprime un enregistrement par son id."""
    try:
        DBDeleteSchema.validate({"table": table, "record_id": record_id})
        result = run_db_pipeline(table=table, action="delete", record_id=record_id, db_path=_db_path())
        return jsonify(ok(result, f"{table}/{record_id} supprimé")), 200
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("db_delete error: %s", exc)
        return jsonify(error(str(exc), 500)), 500


# ---------------------------------------------------------------------------
# CV generation — FR
# ---------------------------------------------------------------------------

@cv_blueprint.route("/generate/fr", methods=["POST"])
def generate_cv_fr():
    """
    Génère le CV FR au format PDF LaTeX.

    Corps JSON requis :
        cv_base_id         : str   — ex: "cv_base_in_all_fr"
        job_id             : str   — ex: "offer-711607447"
    Corps JSON optionnel :
        target_title_index : int   — index dans target_titles ; absent = auto
        db_path            : str   — chemin custom vers jobcv.db
    """
    body = request.get_json(silent=True) or {}
    try:
        CVGenerateFRSchema.validate(body)
        result = run_cv_fr_pipeline(
            cv_base_id=body["cv_base_id"],
            job_id=body["job_id"],
            db_path=body.get("db_path") or _DEFAULT_DB_PATH,
            target_title_index=body.get("target_title_index"),
        )
        if not result:
            return jsonify(error("Échec de la génération du CV.", 500)), 500
        return jsonify(ok(result, "CV généré")), 200
    except ValueError as exc:
        return jsonify(error(str(exc), 400)), 400
    except Exception as exc:
        logger.exception("generate_cv_fr error: %s", exc)
        return jsonify(error(str(exc), 500)), 500
