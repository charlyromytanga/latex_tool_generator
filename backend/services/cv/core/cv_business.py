# *-- UTF-8 --*

# =======IMPORTS========
import os
import json
import logging
import sys
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Imports compatibles exécution directe ET import package
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
try:
    from .cv_utils import CV, CVLatexGeneratorFR
    try:
        from .cv_utils import IntegrationService  # type: ignore
    except ImportError:
        IntegrationService = None  # type: ignore
except ImportError:
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    from backend.services.cv.core.cv_utils import CV, CVLatexGeneratorFR  # type: ignore
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
OFFER_TEXT_PATH = os.path.join(OFFERS_DIR, "offer_text_1.txt")





# ========PIPELINE CV FR — GÉNÉRATION PDF LATEX========

_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "backend", "db", "jobcv.db")

def run_cv_fr_pipeline(
    cv_base_id: str,
    job_id: str,
    db_path: str = _DEFAULT_DB_PATH,
    target_title_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Génère le CV FR au format PDF à partir des données SQLite.

    Args:
        cv_base_id: ID de la ligne cv_base.
        job_id: ID de la ligne jobs.
        db_path: Chemin vers jobcv.db.
        target_title_index: Sélection du titre de poste visé.
            None (défaut) → auto : job_title de l'offre si renseigné, sinon target_titles[0]
            0  → Market Risk Analyst  (candidature spontanée, index 0)
            1  → Trading Analyst      (candidature spontanée, index 1)
            2  → Data Analyst         (candidature spontanée, index 2)
            n  → target_titles[n]

    Returns:
        {"tex": <path>, "pdf": <path>} ou {} en cas d'erreur.
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("DÉMARRAGE PIPELINE CV FR — LATEX")
    logger.info("=" * 60)
    logger.info("  cv_base_id         : %s", cv_base_id)
    logger.info("  job_id             : %s", job_id)
    logger.info("  db_path            : %s", db_path)
    logger.info("  target_title_index : %s", target_title_index)

    try:
        gen = CVLatexGeneratorFR.from_db(
            db_path=db_path,
            cv_base_id=cv_base_id,
            job_id=job_id,
            target_title_index=target_title_index,
        )
        logger.info("CVLatexGeneratorFR chargé — cv_base: %s | job: %s @ %s",
                    gen.cv.get("id"), gen.job.get("company_name"), gen.job.get("city"))
    except Exception as e:
        logger.exception("Erreur chargement CVLatexGeneratorFR : %s", e)
        return {}

    try:
        tex_path, pdf_path = gen.generate()
        logger.info("")
        logger.info("PIPELINE CV FR TERMINÉ")
        logger.info("  TEX → %s", tex_path)
        logger.info("  PDF → %s", pdf_path)
        logger.info("=" * 60)
        return {"tex": str(tex_path), "pdf": str(pdf_path)}
    except Exception as e:
        logger.exception("Erreur génération CV FR : %s", e)
        return {}


# ========EXÉCUTION DIRECTE========
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline CV")
    parser.add_argument(
        "--mode",
        choices=["full", "cv-fr"],
        default="full",
        help="full = pipeline LLM 3 étapes | cv-fr = génération PDF LaTeX FR",
    )
    parser.add_argument("--cv-base-id", default=os.getenv("CV_BASE_ID", ""), help="ID cv_base (mode cv-fr)")
    parser.add_argument("--job-id", default=os.getenv("JOB_ID", ""), help="ID job_offer (mode cv-fr)")
    parser.add_argument("--db-path", default=_DEFAULT_DB_PATH, help="Chemin vers jobcv.db (mode cv-fr)")
    parser.add_argument(
        "--target-title-index",
        type=int,
        default=None,
        help=(
            "Index du titre de poste visé dans cv_base.target_titles (candidature spontanée). "
            "Non fourni = auto (job_title de l'offre si dispo, sinon index 0). "
            "Ex: 0=Market Risk Analyst, 1=Trading Analyst, 2=Data Analyst"
        ),
    )
    args = parser.parse_args()

    # ── MODE cv-fr : génération PDF LaTeX ────────────────────────────────────
    if args.mode == "cv-fr":
        if not args.cv_base_id or not args.job_id:
            logger.error("--cv-base-id et --job-id sont requis pour le mode cv-fr")
            sys.exit(1)

        result = run_cv_fr_pipeline(
            cv_base_id=args.cv_base_id,
            job_id=args.job_id,
            db_path=args.db_path,
            target_title_index=args.target_title_index,
        )
        sys.exit(0 if result else 1)
