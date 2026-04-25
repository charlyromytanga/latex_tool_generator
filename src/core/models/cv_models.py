# *-- UTF-8 --*

# =======IMPORTS========
import os
import json
import logging
import sys
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

# Imports compatibles exécution directe (python -m) ET import package
try:
    from ..utils.cv_pipeline import CV, IntegrationService
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from core.utils.cv_pipeline import CV, IntegrationService  # type: ignore

# ========CONFIG LOGGING========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ========CHEMINS — résolus depuis la racine du projet========
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_DIR = os.path.join(_PROJECT_ROOT, os.getenv("DATA_DIR", "data").lstrip("./"))
OFFERS_DIR = os.path.join(_PROJECT_ROOT, os.getenv("OFFERS_DIR", "data/offers").lstrip("./"))
OFFER_TEXT_PATH = os.path.join(OFFERS_DIR, "offer_text_1.txt")


# ========PIPELINE CV — CHARGEMENT BASE========
logger.info("=" * 60)
logger.info("INITIALISATION PIPELINE CV")
logger.info("=" * 60)

cv = CV(data_dir=DATA_DIR)

logger.info("Chargement formations / expériences / projets...")
formations, experiences, projects = cv.load_alls()
logger.info(f"  → {len(formations)} formations | {len(experiences)} expériences | {len(projects)} projets")

logger.info("Construction cv_base_in_all FR + EN...")
cv_base_in_all_fr, cv_base_in_all_en = cv.cv_base_in_all()
logger.info(f"  → CV base FR sections : {list(cv_base_in_all_fr.keys())}")
logger.info(f"  → CV base EN sections : {list(cv_base_in_all_en.keys())}")


# ========INSTANCIATION IntegrationService========
logger.info("Instanciation IntegrationService...")
integration_service = IntegrationService(
    cv_base_fr=cv_base_in_all_fr,
    cv_base_en=cv_base_in_all_en,
    n8n_webhook_url=os.getenv("N8N_WEBHOOK_URL", ""),
)
logger.info("  → IntegrationService prêt (modèles : %s / scoring : %s)",
            integration_service.model, integration_service.model_scoring)


# ========PIPELINE COMPLET : 3 ÉTAPES========

def run_full_pipeline(offer_text: str) -> Dict[str, Any]:
    """
    Simule le flux complet de la web app Streamlit :
      Étape 1 → POST /offer_input          (extraction + structuration)
      Étape 2 → POST /offer_upgrade_by_llm (enrichissement LLM + sauvegarde job_offer)
      Étape 3 → POST /score_and_cv_lm      (scoring ATS + génération CV/LM si ≥ 70 %)
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("DÉMARRAGE PIPELINE COMPLET")
    logger.info("=" * 60)
    logger.info("Taille de l'offre texte : %d caractères", len(offer_text))

    # ─── ÉTAPE 1 : extraction et structuration ───────────────────────────────
    logger.info("")
    logger.info("─" * 50)
    logger.info("ÉTAPE 1 — extraction et structuration de l'offre")
    logger.info("─" * 50)

    try:
        step1_result = integration_service.extract_and_structure_offer(offer_text)

        if not step1_result:
            logger.error("ÉTAPE 1 ÉCHOUÉE — résultat vide")
            return {}

        structured_offer: Dict[str, Any] = step1_result["structured_offer"]

        logger.info("OUTPUT ÉTAPE 1 — offre structurée :")
        logger.info("  id            : %s", structured_offer.get("id"))
        logger.info("  language      : %s", structured_offer.get("language"))
        logger.info("  country       : %s", structured_offer.get("country"))
        logger.info("  city          : %s", structured_offer.get("city"))
        logger.info("  compagny_name : %s", structured_offer.get("compagny_name"))
        logger.info("  compagny_type : %s", structured_offer.get("compagny_type"))
        logger.info("  offer_title   : %s", structured_offer.get("offer_title"))
        logger.info("  llm_header    : %s", structured_offer.get("llm_header"))
        logger.info(
            "  offer_description [%d chars] : %s...",
            len(str(structured_offer.get("offer_description", ""))),
            str(structured_offer.get("offer_description", ""))[:120],
        )

    except Exception as e:
        logger.exception("Exception non gérée à l'ÉTAPE 1 : %s", e)
        return {}

    # ─── ÉTAPE 2 : enrichissement LLM croisé avec cv_base ───────────────────
    logger.info("")
    logger.info("─" * 50)
    logger.info("ÉTAPE 2 — enrichissement LLM + sauvegarde job_offer")
    logger.info("─" * 50)

    try:
        full_offer: Dict[str, Any] = integration_service.enrich_offer_with_cv(
            structured_offer=structured_offer,
            offer_text=offer_text,
        )

        if not full_offer:
            logger.error("ÉTAPE 2 ÉCHOUÉE — résultat vide")
            return {}

        logger.info("OUTPUT ÉTAPE 2 — offre enrichie (sections LLM) :")
        llm_sections = [
            "llm_summary", "llm_skills", "llm_experience",
            "llm_education", "llm_certifications",
            "llm_projects", "llm_languages", "llm_interests",
        ]
        for key in llm_sections:
            val = str(full_offer.get(key, ""))
            logger.info("  %s [%d chars] : %s...", key, len(val), val[:100])

    except Exception as e:
        logger.exception("Exception non gérée à l'ÉTAPE 2 : %s", e)
        return {}

    # ─── ÉTAPE 3 : scoring ATS + génération CV / LM ──────────────────────────
    logger.info("")
    logger.info("─" * 50)
    logger.info("ÉTAPE 3 — scoring ATS + génération CV/LM si score ≥ 70 %%")
    logger.info("─" * 50)

    try:
        score_result: Dict[str, Any] = integration_service.score_and_generate(full_offer)

        if not score_result:
            logger.error("ÉTAPE 3 ÉCHOUÉE — résultat vide")
            return {}

        score = score_result.get("score", 0.0)
        logger.info("OUTPUT ÉTAPE 3 — scoring :")
        logger.info("  candidature_id     : %s", score_result.get("candidature_id"))
        logger.info("  job_offer_id       : %s", score_result.get("job_offer_id"))
        logger.info("  score ATS          : %.2f (%.0f %%)", score, score * 100)
        logger.info("  documents générés  : %s", score_result.get("documents_generated"))
        logger.info("  justification      : %s", score_result.get("justification"))

        details = score_result.get("score_details") or {}
        for k, v in details.items():
            logger.info("    détail %-20s : %.2f", k, v)

        if score_result.get("documents_generated"):
            cv_text = str(score_result.get("cv", ""))
            lm_text = str(score_result.get("lm", ""))
            logger.info("  CV généré  [%d chars] : %s...", len(cv_text), cv_text[:150])
            logger.info("  LM générée [%d chars] : %s...", len(lm_text), lm_text[:150])
        else:
            logger.info("  Score < 70 %% — aucun document généré")

    except Exception as e:
        logger.exception("Exception non gérée à l'ÉTAPE 3 : %s", e)
        return {}

    # ─── Résumé final ─────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE TERMINÉ")
    logger.info("  Offre ID       : %s", full_offer.get("id"))
    logger.info("  Candidature ID : %s", score_result.get("candidature_id"))
    logger.info("  Score ATS      : %.0f %%", (score_result.get("score", 0.0)) * 100)
    logger.info("  Documents      : %s", score_result.get("documents_generated"))
    logger.info("=" * 60)

    return {
        "step1": step1_result,
        "step2": full_offer,
        "step3": score_result,
    }


# ========EXÉCUTION DIRECTE========
if __name__ == "__main__":
    logger.info("Lecture de l'offre : %s", OFFER_TEXT_PATH)

    try:
        with open(OFFER_TEXT_PATH, "r", encoding="utf-8") as f:
            offer_text = f.read().strip()
        logger.info("Offre chargée (%d caractères)", len(offer_text))
    except FileNotFoundError:
        logger.error("Fichier introuvable : %s", OFFER_TEXT_PATH)
        sys.exit(1)
    except Exception as e:
        logger.exception("Erreur lecture fichier : %s", e)
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "").startswith("your_"):
        logger.error("ANTHROPIC_API_KEY non définie — définis-la avant de lancer le pipeline")
        sys.exit(1)

    result = run_full_pipeline(offer_text)

    if result:
        output_path = os.path.join(DATA_DIR, "pipeline_output_last.json")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info("Résultat complet sauvegardé → %s", output_path)
        except Exception as e:
            logger.warning("Impossible de sauvegarder le JSON de sortie : %s", e)
