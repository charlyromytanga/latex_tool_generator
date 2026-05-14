# *-- UTF-8 --*

# =======IMPORTS========
import os
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Imports compatibles exécution directe ET import package
def _resolve_repo_root() -> str:
    candidates = []
    project_root_env = os.getenv("PROJECT_ROOT")
    if project_root_env:
        candidates.append(Path(project_root_env).resolve())
    candidates.append(Path.cwd().resolve())
    module_path = Path(__file__).resolve()
    candidates.extend(module_path.parents)

    for candidate in candidates:
        if (candidate / "backend").exists() and (candidate / "shared").exists():
            return str(candidate)

    return str(module_path.parents[4])


_REPO_ROOT = _resolve_repo_root()
try:
    from .cv_utils import DatabaseManager, CVLatexGeneratorFR, CVLatexGeneratorEN
    try:
        from .cv_utils import IntegrationService  # type: ignore
    except ImportError:
        IntegrationService = None  # type: ignore
except ImportError:
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    from backend.services.cv.core.cv_utils import DatabaseManager, CVLatexGeneratorFR, CVLatexGeneratorEN  # type: ignore
    try:
        from backend.services.cv.core.cv_utils import IntegrationService  # type: ignore
    except ImportError:
        IntegrationService = None  # type: ignore

# ========CONFIG LOGGING========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ========CHEMINS — résolus depuis la racine du projet========
_PROJECT_ROOT = _REPO_ROOT
DATA_DIR = os.path.join(_PROJECT_ROOT, os.getenv("DATA_DIR", "data").lstrip("./"))
OFFERS_DIR = os.path.join(_PROJECT_ROOT, os.getenv("OFFERS_DIR", "data/offers").lstrip("./"))
DOCS_OFFERS_DIR = os.path.join(_PROJECT_ROOT, "docs", "offers")
OFFER_TEXT_PATH = os.path.join(OFFERS_DIR, "offer_text_1.txt")
_DEFAULT_DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(_PROJECT_ROOT, "db", "jobcv.db"),
)


def _job_to_offer_json_payload(job: Dict[str, Any]) -> Dict[str, Any]:
    offer_id = str(job.get("id") or "")
    reference = offer_id.removeprefix("offer-") if offer_id else ""
    return {
        "id": offer_id,
        "reference": reference,
        "language": job.get("language"),
        "country": job.get("country"),
        "city": job.get("city"),
        "company_name": job.get("company_name"),
        "company_type": job.get("company_type"),
        "offer_title": job.get("job_title"),
        "offer_description": job.get("offer_description"),
        "company_presentation": job.get("company_presentation"),
        "job_title": job.get("job_title"),
    }


def _write_job_offer_json(job: Dict[str, Any]) -> str:
    offer_id = str(job.get("id") or "").strip()
    if not offer_id:
        raise ValueError("Impossible d'écrire le JSON offre sans id.")
    os.makedirs(DOCS_OFFERS_DIR, exist_ok=True)
    json_path = os.path.join(DOCS_OFFERS_DIR, f"{offer_id}.json")
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(_job_to_offer_json_payload(job), handle, ensure_ascii=False, indent=2)
    return json_path


def _delete_job_offer_json(record_id: str) -> None:
    json_path = os.path.join(DOCS_OFFERS_DIR, f"{record_id}.json")
    if os.path.exists(json_path):
        os.remove(json_path)


# ========PIPELINE DB — INGESTION MISE A JOUR TABLES ========
def _run_cv_base_ingest(db_path: str, source_path: Optional[str] = None) -> Any:
    """Helper : charge l'ingesteur cv_base via importlib (évite __init__.py de shared/db_orchestration)."""
    import importlib.util as _ilu
    from pathlib import Path as _Path
    _ingestor_path = _Path(_REPO_ROOT) / "shared" / "db_orchestration" / "cv_base_ingestor.py"
    _spec = _ilu.spec_from_file_location("cv_base_ingestor", _ingestor_path)
    _mod = _ilu.module_from_spec(_spec)  # type: ignore
    sys.modules["cv_base_ingestor"] = _mod
    _spec.loader.exec_module(_mod)  # type: ignore
    orch = _mod.CVBaseIngestionOrchestrator(db_path=db_path)
    if source_path:
        return orch.run_from_file(_Path(source_path))
    return orch.run_all()


def run_db_pipeline(
    table: str,
    action: str,
    record_id: str,
    data: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    db_path: str = _DEFAULT_DB_PATH,
    source_path: Optional[str] = None,
) -> Any:
    """
    Pipeline de gestion des tables SQLite via DatabaseManager.

    Args:
        table      : Nom de la table cible — 'cv_base' | 'jobs' | 'cv_applications' | 'applications'
        action     : Opération — 'add' | 'get' | 'update' | 'delete' | 'list' | 'summary' | 'ingest'
        record_id  : ID de l'enregistrement (requis pour get, update, delete)
        data       : Dict pour update (cv_base) ; ignoré pour add (source JSON utilisée)
        filters    : Dict de filtres pour list (ex: {"language": "fr"})
        db_path    : Chemin vers jobcv.db
        source_path: Fichier JSON source dans docs/cv_base/ (add/ingest cv_base ;
                     si absent → tous les fichiers de docs/cv_base/)

    Returns:
        - add/ingest (cv_base) → list[dict] résultats par fichier
        - add (autres tables)  → int ou None
        - update/delete        → int ou None
        - get                  → dict ou None
        - list                 → list[dict]
        - summary              → dict {table: count}
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE DB — table=%s | action=%s | id=%s", table, action, record_id)
    logger.info("=" * 60)

    db = DatabaseManager(db_path)

    if action == "summary":
        result = db.summary()
        logger.info("Résumé DB : %s", result)
        return result

    # Pour cv_base : add et ingest passent tous deux par l'ingesteur JSON (docs/cv_base/)
    if table == "cv_base" and action in ("add", "ingest"):
        result = _run_cv_base_ingest(db_path=db_path, source_path=source_path)
        logger.info("INGEST cv_base terminé → %s", result)
        return result

    def _add_job_and_sync() -> int | None:
        payload = data or {}
        db.add_job(payload)
        job = db.get_job(str(payload.get("id") or ""))
        if job:
            json_path = _write_job_offer_json(job)
            logger.info("JSON job écrit → %s", json_path)
        return 1

    def _update_job_and_sync() -> int | None:
        updated = db.update_job(record_id, **(data or {}))
        job = db.get_job(record_id)
        if job:
            json_path = _write_job_offer_json(job)
            logger.info("JSON job mis à jour → %s", json_path)
        return updated

    def _delete_job_and_sync() -> int | None:
        deleted = db.delete_job(record_id)
        if deleted:
            _delete_job_offer_json(record_id)
            logger.info("JSON job supprimé → %s", record_id)
        return deleted

    # Dispatcher table × action pour les autres cas
    _dispatch: Dict[str, Dict[str, Any]] = {
        "cv_base": {
            "get":     lambda: db.get_cv_base(record_id),
            "update":  lambda: db.update_cv_base(record_id, **(data or {})),
            "delete":  lambda: db.delete_cv_base(record_id),
            "list":    lambda: db.list_cv_bases(**(filters or {})),
        },
        "jobs": {
            "add":     _add_job_and_sync,
            "get":     lambda: db.get_job(record_id),
            "update":  _update_job_and_sync,
            "delete":  _delete_job_and_sync,
            "list":    lambda: db.list_jobs(**(filters or {})),
        },
        "cv_applications": {
            "add":     lambda: db.add_cv_application(data or {}),
            "get":     lambda: db.get_cv_application(record_id),
            "update":  lambda: db.update_cv_application(record_id, **(data or {})),
            "delete":  lambda: db.delete_cv_application(record_id),
            "list":    lambda: db.list_cv_applications(**(filters or {})),
        },
        "applications": {
            "add":     lambda: db.add_application(data or {}),
            "get":     lambda: db.get_application(record_id),
            "update":  lambda: db.update_application(record_id, **(data or {})),
            "delete":  lambda: db.delete_application(record_id),
            "list":    lambda: db.list_applications(**(filters or {})),
        },
    }

    if table not in _dispatch:
        raise ValueError(f"Table inconnue : '{table}'. Valeurs valides : {list(_dispatch)}")
    if action not in _dispatch[table]:
        raise ValueError(f"Action inconnue : '{action}'. Valeurs valides pour '{table}' : {list(_dispatch[table])}")

    try:
        result = _dispatch[table][action]()
        logger.info("PIPELINE DB TERMINÉ → %s", result)
        return result
    except Exception as e:
        logger.exception("Erreur pipeline DB : %s", e)
        return None







# ========PIPELINE CV — GÉNÉRATION PDF LATEX========

def _run_cv_pipeline(
    language: str,
    cv_base_id: str,
    job_id: str,
    job_title: str,
    db_path: str = _DEFAULT_DB_PATH,
    target_title_index: Optional[int] = None,
    max_projects: int = 10,
    max_experiences: int = 8,
    max_competences: int = 2,
    max_competences_techniques: int = 3,
    selected_project_indices: Optional[List[int]] = None,
    selected_experience_indices: Optional[List[int]] = None,
    selected_competence_indices: Optional[List[int]] = None,
    selected_competence_technique_indices: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Génère un CV PDF LaTeX à partir des données SQLite.

    Args:
        language: Langue du rendu, fr ou en.
        cv_base_id: ID de la ligne cv_base.
        job_id: ID de la ligne jobs.
        db_path: Chemin vers jobcv.db.
        target_title_index: Sélection du titre de poste visé.
            None (défaut) → auto : job_title de l'offre si renseigné, sinon target_titles[0]
            1  → Market Risk Analyst
            2  → Trading Analyst
            3  → Data Analyst
            n  → target_titles[n - 1]
        max_projects / max_experiences / max_competences / max_competences_techniques :
            Nombre maximum d'items affichés par section (plafond).
        selected_*_indices: Liste d'indices (0-based) à inclure (avant application du max).
            None = tous les items disponibles.

    Returns:
        {"tex": <path>, "pdf": <path>} ou {} en cas d'erreur.
    """
    language = (language or "fr").lower()
    if target_title_index == 0:
        target_title_index = None

    logger.info("")
    logger.info("=" * 60)
    logger.info("DÉMARRAGE PIPELINE CV %s — LATEX", language.upper())
    logger.info("=" * 60)
    logger.info("  language                          : %s", language)
    logger.info("  cv_base_id                        : %s", cv_base_id)
    logger.info("  job_id                            : %s", job_id)
    logger.info("  db_path                           : %s", db_path)
    logger.info("  target_title_index                : %s", target_title_index)
    logger.info("  max_projects                      : %s", max_projects)
    logger.info("  max_experiences                   : %s", max_experiences)
    logger.info("  max_competences                   : %s", max_competences)
    logger.info("  max_competences_techniques        : %s", max_competences_techniques)
    logger.info("  selected_project_indices          : %s", selected_project_indices)
    logger.info("  selected_experience_indices       : %s", selected_experience_indices)
    logger.info("  selected_competence_indices       : %s", selected_competence_indices)
    logger.info("  selected_competence_tech_indices  : %s", selected_competence_technique_indices)

    try:
        generator_class = CVLatexGeneratorEN if language == "en" else CVLatexGeneratorFR
        gen = generator_class.from_db(
            db_path=db_path,
            cv_base_id=cv_base_id,
            job_id=job_id,
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
        logger.info("%s chargé — cv_base: %s | job: %s @ %s",
                    generator_class.__name__,
                    gen.cv.get("id"), gen.job.get("company_name"), gen.job.get("city"))
    except Exception as e:
        logger.exception("Erreur chargement générateur CV %s : %s", language.upper(), e)
        return {}

    try:
        tex_path, pdf_path = gen.generate()
        logger.info("")
        logger.info("PIPELINE CV %s TERMINÉ", language.upper())
        logger.info("  TEX → %s", tex_path)
        logger.info("  PDF → %s", pdf_path)
        logger.info("=" * 60)
        return {"tex": str(tex_path), "pdf": str(pdf_path)}
    except Exception as e:
        logger.exception("Erreur génération CV %s : %s", language.upper(), e)
        return {}


def run_cv_fr_pipeline(
    cv_base_id: str,
    job_id: str,
    job_title: str,
    db_path: str = _DEFAULT_DB_PATH,
    target_title_index: Optional[int] = None,
    max_projects: int = 10,
    max_experiences: int = 8,
    max_competences: int = 2,
    max_competences_techniques: int = 3,
    selected_project_indices: Optional[List[int]] = None,
    selected_experience_indices: Optional[List[int]] = None,
    selected_competence_indices: Optional[List[int]] = None,
    selected_competence_technique_indices: Optional[List[int]] = None,
) -> Dict[str, Any]:
    return _run_cv_pipeline(
        language="fr",
        cv_base_id=cv_base_id,
        job_id=job_id,
        job_title=job_title,
        db_path=db_path,
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


def run_cv_en_pipeline(
    cv_base_id: str,
    job_id: str,
    job_title: str,
    db_path: str = _DEFAULT_DB_PATH,
    target_title_index: Optional[int] = None,
    max_projects: int = 10,
    max_experiences: int = 8,
    max_competences: int = 2,
    max_competences_techniques: int = 3,
    selected_project_indices: Optional[List[int]] = None,
    selected_experience_indices: Optional[List[int]] = None,
    selected_competence_indices: Optional[List[int]] = None,
    selected_competence_technique_indices: Optional[List[int]] = None,
) -> Dict[str, Any]:
    return _run_cv_pipeline(
        language="en",
        cv_base_id=cv_base_id,
        job_id=job_id,
        job_title=job_title,
        db_path=db_path,
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


# ========EXÉCUTION DIRECTE========
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline CV & DB — Gestion des tables et génération PDF LaTeX"
    )
    parser.add_argument(
        "--mode",
        choices=["cv-fr", "cv-en", "db"],
        required=True,
        help="cv-fr = génération PDF LaTeX FR | cv-en = génération PDF LaTeX EN | db = gestion des tables SQLite",
    )

    # ── Arguments mode cv-fr ─────────────────────────────────────────────────
    parser.add_argument("--cv-base-id", default=os.getenv("CV_BASE_ID", ""), help="ID cv_base")
    parser.add_argument("--job-id",     default=os.getenv("JOB_ID", ""),     help="ID job_offer")
    parser.add_argument("--db-path",    default=_DEFAULT_DB_PATH,             help="Chemin vers jobcv.db")
    parser.add_argument(
        "--target-title-index",
        type=int,
        default=None,
        help=(
            "Code 1-based du titre de poste visé dans cv_base.target_titles. "
            "Non fourni = auto. Ex: 1=Market Risk Analyst, 2=Trading Analyst, 3=Data Analyst"
        ),
    )
    parser.add_argument("--max-projects",              type=int, default=10, help="Nb max de projets affichés (défaut: 10)")
    parser.add_argument("--max-experiences",           type=int, default=8,  help="Nb max d'expériences affichées (défaut: 8)")
    parser.add_argument("--max-competences",           type=int, default=2,  help="Nb max de compétences (défaut: 2)")
    parser.add_argument("--max-competences-techniques",type=int, default=3,  help="Nb max de connaissances techniques (défaut: 3)")
    parser.add_argument("--project-indices",              nargs="*", type=int, default=None, metavar="N", help="Indices (0-based) des projets à inclure")
    parser.add_argument("--experience-indices",           nargs="*", type=int, default=None, metavar="N", help="Indices (0-based) des expériences à inclure")
    parser.add_argument("--competence-indices",           nargs="*", type=int, default=None, metavar="N", help="Indices (0-based) des compétences à inclure")
    parser.add_argument("--competence-technique-indices", nargs="*", type=int, default=None, metavar="N", help="Indices (0-based) des connaissances techniques à inclure")

    # ── Arguments mode db ────────────────────────────────────────────────────
    parser.add_argument(
        "--table",
        choices=["cv_base", "jobs", "cv_applications", "applications"],
        help="Table cible (mode db)",
    )
    parser.add_argument(
        "--action",
        choices=["add", "get", "update", "delete", "list", "summary", "ingest"],
        help="Opération CRUD (mode db) ; 'ingest' lit les sources JSON de docs/cv_base/",
    )
    parser.add_argument("--id",      default=None, help="ID de l'enregistrement (get/update/delete)")
    parser.add_argument("--data",    default=None, help="JSON dict pour add/update (ex: '{\"id\":\"x\",\"language\":\"fr\"}')")
    parser.add_argument("--filters", default=None, help="JSON dict de filtres pour list (ex: '{\"language\":\"fr\"}')")
    parser.add_argument(
        "--source",
        default=None,
        metavar="FILENAME",
        help=(
            "Nom du fichier JSON source dans docs/<table>/ pour add/ingest. "
            "Ex: cv_base_fr.json  →  résolu en docs/cv_base/cv_base_fr.json. "
            "Si absent, tous les fichiers du répertoire sont ingérés."
        ),
    )

    args = parser.parse_args()

    # ── MODE cv-fr / cv-en ───────────────────────────────────────────────────
    if args.mode in {"cv-fr", "cv-en"}:
        if not args.cv_base_id or not args.job_id:
            logger.error("--cv-base-id et --job-id sont requis pour les modes cv-fr/cv-en")
            sys.exit(1)
        pipeline = run_cv_en_pipeline if args.mode == "cv-en" else run_cv_fr_pipeline
        result = pipeline(
            cv_base_id=args.cv_base_id,
            job_id=args.job_id,
            job_title="",
            db_path=args.db_path,
            target_title_index=args.target_title_index,
            max_projects=args.max_projects,
            max_experiences=args.max_experiences,
            max_competences=args.max_competences,
            max_competences_techniques=args.max_competences_techniques,
            selected_project_indices=args.project_indices,
            selected_experience_indices=args.experience_indices,
            selected_competence_indices=args.competence_indices,
            selected_competence_technique_indices=args.competence_technique_indices,
        )
        sys.exit(0 if result else 1)

    # ── MODE db ───────────────────────────────────────────────────────────────
    if args.mode == "db":
        if args.action != "summary" and not args.table:
            logger.error("--table est requis pour le mode db (sauf action=summary)")
            sys.exit(1)
        if not args.action:
            logger.error("--action est requis pour le mode db")
            sys.exit(1)

        data    = json.loads(args.data)    if args.data    else None
        filters = json.loads(args.filters) if args.filters else None

        # Résolution du nom de fichier court → chemin complet dans docs/<table>/
        source_path = None
        if args.source:
            _docs_dir = os.path.join(_PROJECT_ROOT, "docs", args.table or "cv_base")
            source_path = os.path.join(_docs_dir, args.source)

        result = run_db_pipeline(
            table=args.table or "",
            action=args.action,
            record_id=args.id,
            data=data,
            filters=filters,
            db_path=args.db_path,
            source_path=source_path,
        )
        if isinstance(result, (list, dict)):
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif result is not None:
            print(result)
        sys.exit(0 if result is not None else 1)
