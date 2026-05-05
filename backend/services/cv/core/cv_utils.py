import os
import json
import re
from pprint import pprint
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
import logging
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

# Insertion SQL dans la base après le dump JSON
import sqlite3
from dotenv import load_dotenv
load_dotenv()
import os

class CV:
    """
    Classe principale pour la gestion et la génération de CV à partir de ressources JSON structurées.
    Permet de charger, organiser et restituer les différentes sections du CV (formations, expériences, projets, etc.)
    en plusieurs langues, avec une compatibilité ATS et une logique modulaire.
    """
    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.formations_dir: str = os.path.join(data_dir, 'formations')
        self.experiences_dir: str = os.path.join(data_dir, 'experiences')
        self.projects_dir: str = os.path.join(data_dir, 'projects')
        self.cv_base_in_alls_dir: str = os.path.join(data_dir, "cv_base_in_alls")

        self.db_dir = os.getenv('DB_DIR', './db')
        self.queries_dir = os.getenv('QUERIES_DIR', './db/requeries')
        self.insert_query_path = os.getenv('INSERT_CV_BASE_IN_ALLS_QUERY', './db/requeries/insert_cv_base_in_alls.sql')


    def load_alls(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Charge toutes les formations, expériences et projets à partir des fichiers JSON présents dans les dossiers dédiés.
        Retourne :
            tuple (formations, experiences, projects)
            - formations : list[dict[str, Any]]
            - experiences : list[dict[str, Any]]
            - projects : list[dict[str, Any]]
        Les éléments sont fusionnés à partir de tous les fichiers .json trouvés dans chaque dossier.
        """

        formations_files: list[str] = [f for f in os.listdir(self.formations_dir) if f.endswith('.json')]
        experiences_files: list[str] = [f for f in os.listdir(self.experiences_dir) if f.endswith('.json')]
        projects_files: list[str] = [f for f in os.listdir(self.projects_dir) if f.endswith('.json')]

        formations: list[dict[str, Any]] = []
        experiences: list[dict[str, Any]] = []
        projects: list[dict[str, Any]] = []

        # Chargement formations
        for file in formations_files:
            try:
                with open(os.path.join(self.formations_dir, file), 'r', encoding='utf-8') as f:
                    data_formations = json.load(f)
                    if isinstance(data_formations, dict) and 'formations' in data_formations:
                        formations.extend([x for x in data_formations['formations'] if isinstance(x, dict)])
                    elif isinstance(data_formations, dict):
                        formations.append(data_formations)
            except Exception as e:
                logger.error(f"Erreur chargement formation {file}: {e}")

        # Chargement expériences
        for file in experiences_files:
            try:
                with open(os.path.join(self.experiences_dir, file), 'r', encoding='utf-8') as f:
                    data_experiences = json.load(f)
                    if isinstance(data_experiences, dict) and 'experiences' in data_experiences:
                        experiences.extend([x for x in data_experiences['experiences'] if isinstance(x, dict)])
                    elif isinstance(data_experiences, dict):
                        experiences.append(data_experiences)
            except Exception as e:
                logger.error(f"Erreur chargement experience {file}: {e}")

        # Chargement projets
        for file in projects_files:
            try:
                with open(os.path.join(self.projects_dir, file), 'r', encoding='utf-8') as f:
                    data_projects = json.load(f)
                    if isinstance(data_projects, dict) and 'projects' in data_projects:
                        projects.extend([x for x in data_projects['projects'] if isinstance(x, dict)])
                    elif isinstance(data_projects, dict):
                        projects.append(data_projects)
            except Exception as e:
                logger.error(f"Erreur chargement projet {file}: {e}")

        return formations, experiences, projects


    def cv_base_in_all(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Construit la base structurée du CV pour chaque langue (français et anglais).
        Charge les différentes sections (formations, expériences, projets, skills, summary, header, etc.)
        à partir des ressources JSON, et assemble un dictionnaire par langue prêt à l'emploi pour l'export ou le matching ATS.
        Retourne :
            tuple (cv_base_in_alls_fr, cv_base_in_alls_en)
            - cv_base_in_alls_fr : dict[str, Any] (sections du CV en français)
            - cv_base_in_alls_en : dict[str, Any] (sections du CV en anglais)
        En cas d'erreur, retourne deux dictionnaires vides.
        """

        try:
            formations, experiences, projects = self.load_alls()
            formations_fr = [f for f in formations if f.get('language') == 'fr']
            formations_en = [f for f in formations if f.get('language') == 'en']
            experiences_fr = [e for e in experiences if e.get('language') == 'fr']
            experiences_en = [e for e in experiences if e.get('language') == 'en']
            projects_fr = [p for p in projects if p.get('language') == 'fr']
            projects_en = [p for p in projects if p.get('language') == 'en']

            self.languages : List[str] = ['fr', 'en']
            self.cv_base_in_all_fr = {}
            self.cv_base_in_all_en = {}

            # chargement formations depuis linkedin_charly_romy_tanga_formations.json
            formations_path = os.path.join(self.data_dir, 'formations', 'linkedin_charly_romy_tanga_formations.json')
            with open(formations_path, 'r', encoding='utf-8') as f:
                formations_data = json.load(f)
            formations_fr = [f['ats_bullet_fr'] for f in formations_data['formations'] if f.get('language') == 'fr']
            formations_en = [f['ats_bullet_en'] for f in formations_data['formations'] if f.get('language') == 'en']

            # Chargement skills
            with open(os.path.join(self.data_dir, 'skills', 'skills.json'), 'r', encoding='utf-8') as f:
                skills_data = json.load(f)
            soft_fr = [s['fr'] for s in skills_data['soft_skills']]
            soft_en = [s['en'] for s in skills_data['soft_skills']]
            hard_fr = [s['fr'] for s in skills_data['hard_skills']]
            hard_en = [s['en'] for s in skills_data['hard_skills']]

            # Chargement summary
            with open(os.path.join(self.data_dir, 'summary', 'summary.json'), 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            summary_fr = summary_data.get('summary_fr', [])
            summary_en = summary_data.get('summary_en', [])

            # Chargement header
            with open(os.path.join(self.data_dir, 'header', 'header.json'), 'r', encoding='utf-8') as f:
                header_data = json.load(f)
            header_fr = header_data.get('header_fr', [])
            header_en = header_data.get('header_en', [])

            self.cv_base_in_all_fr = {
                "header": "\n".join(header_fr),
                "summary": "\n".join([f"• {b}" for b in summary_fr]),
                "skills": "\n".join([f"• {b}" for b in soft_fr + hard_fr]),
                "experience": "\n".join([f"• {e.get('ats_bullet_fr', '')}" for e in experiences_fr]),
                "education": "\n".join([f"• {b}" for b in formations_fr]),
                "certifications": "Microsoft Data Analyst (en cours), BMC (en cours), AMF (en cours)",
                "projects": "\n".join([f"• {p.get('ats_bullet_fr', '')}" for p in projects_fr]),
                "languages": "Français : bilingue ; Anglais : C1 ; Allemand : B1",
                "interests": "Randonnée, musique classique, cyclisme loisir, football loisir",
            }
            self.cv_base_in_all_en = {
                "header": "\n".join(header_en),
                "summary": "\n".join([f"• {b}" for b in summary_en]),
                "skills": "\n".join([f"• {b}" for b in soft_en + hard_en]),
                "experience": "\n".join([f"• {e.get('ats_bullet_en', '')}" for e in experiences_en]),
                "education": "\n".join([f"• {b}" for b in formations_en]),
                "certifications": "Microsoft Data Analyst (in progress), BMC (in progress), AMF (in progress)",
                "projects": "\n".join([f"• {p.get('ats_bullet_en', '')}" for p in projects_en]),
                "languages": "French: bilingual; English: C1; German: B1",
                "interests": "Hiking, classical music, leisure cycling, leisure football",
            }

            # Dump JSON des deux CV dans le dossier dédié
            os.makedirs(self.cv_base_in_alls_dir, exist_ok=True)
            with open(os.path.join(self.cv_base_in_alls_dir, "cv_base_in_all_fr.json"), "w", encoding="utf-8") as f_fr:
                json.dump(self.cv_base_in_all_fr, f_fr, ensure_ascii=False, indent=2)
            with open(os.path.join(self.cv_base_in_alls_dir, "cv_base_in_all_en.json"), "w", encoding="utf-8") as f_en:
                json.dump(self.cv_base_in_all_en, f_en, ensure_ascii=False, indent=2)


            # Insertion FR
            values_fr = (
                'cv_base_in_all_fr',
                'fr',
                self.cv_base_in_all_fr['header'],
                self.cv_base_in_all_fr['summary'],
                self.cv_base_in_all_fr['skills'],
                self.cv_base_in_all_fr['experience'],
                self.cv_base_in_all_fr['education'],
                self.cv_base_in_all_fr['certifications'],
                self.cv_base_in_all_fr['projects'],
                self.cv_base_in_all_fr['languages'],
                self.cv_base_in_all_fr['interests'],
            )
            # Insertion EN
            values_en = (
                'cv_base_in_all_en',
                'en',
                self.cv_base_in_all_en['header'],
                self.cv_base_in_all_en['summary'],
                self.cv_base_in_all_en['skills'],
                self.cv_base_in_all_en['experience'],
                self.cv_base_in_all_en['education'],
                self.cv_base_in_all_en['certifications'],
                self.cv_base_in_all_en['projects'],
                self.cv_base_in_all_en['languages'],
                self.cv_base_in_all_en['interests'],
            )
            sql = '''INSERT OR REPLACE INTO cv_base_in_all (
                id, language, header, summary, skills, experience, education, certifications, projects, languages, interests
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
            try:
                with sqlite3.connect(os.path.join(self.db_dir, "recruitment.db")) as conn:
                    cur = conn.cursor()
                    cur.execute(sql, values_fr)
                    cur.execute(sql, values_en)
                    conn.commit()
            except Exception as sql_e:
                logger.error(f"Erreur lors de l'insertion dans cv_base_in_all : {sql_e}")

            return self.cv_base_in_all_fr, self.cv_base_in_all_en
        except Exception as e:
            logger.error(f"Erreur dans cv_base_in_all : {e}")
            return {}, {}



# --- Classe pour la gestion des offres enrichies ---
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

# --- Classe pour le suivi des candidatures et génération CV/LM ---
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

# --- Classe d'intégration pour LLM Claude et n8n ---
import anthropic
import requests as http_requests
import uuid as uuid_lib

class IntegrationService:
    """
    Gère l'intégration avec Claude (LLM) pour la génération des sections LLM et avec n8n.
    Pipeline en 3 méthodes : extraction → enrichissement → scoring + génération documents.
    """
    def __init__(
        self,
        cv_base_fr: dict,
        cv_base_en: dict,
        n8n_webhook_url: str = "",
        model: str = "claude-sonnet-4-6",
        model_scoring: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
    ):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.model_scoring = model_scoring
        self.max_tokens = max_tokens
        self.cv_base_fr = cv_base_fr
        self.cv_base_en = cv_base_en
        self.n8n_webhook_url = n8n_webhook_url
        self.db_dir = os.getenv("DB_DIR", "./db")

        # Prompts construits à l'instanciation — stables, mis en cache côté Anthropic
        self.prompt_extract = self._build_prompt_extract()
        self.prompt_enrich: Dict[str, str] = {
            "fr": self._build_prompt_enrich("fr"),
            "en": self._build_prompt_enrich("en"),
        }
        self.prompt_score = self._build_prompt_score()

    # ─── Builders de prompts ──────────────────────────────────────────────────

    def _build_prompt_extract(self) -> str:
        return """Tu es un expert en analyse d'offres d'emploi. Extrais les informations structurées d'une offre et retourne un JSON strict.

Règles d'extraction :
- language : langue de l'offre → "fr" ou "en" uniquement
- country : pays du poste → valeurs autorisées uniquement : "fr", "uk", "lu", "de", "ch"
- city : ville (string ou null)
- compagny_name : nom de l'entreprise (string ou null)
- compagny_type : type → valeurs autorisées : "grand groupe", "tpe", "pme", "esn", "banque", "assurance", "industrie", "cabinet conseil", ou null
- offer_title : intitulé exact du poste
- offer_description : description complète du poste (texte brut intégral, ne pas tronquer)
- compagny_presentation : présentation de l'entreprise (string ou null)
- llm_header : reformulation ATS du titre → verbe d'action + domaine + niveau (ex: "Analyste Données Senior | Power BI & Python | Finance")

Retourne UNIQUEMENT le JSON valide, sans markdown ni commentaires."""

    def _build_prompt_enrich(self, language: str) -> str:
        cv_base = self.cv_base_fr if language == "fr" else self.cv_base_en
        cv_json = json.dumps(cv_base, ensure_ascii=False, indent=2)
        lang_label = "français" if language == "fr" else "anglais"
        return f"""
                Tu es un expert ATS (Applicant Tracking System). Tu personnalises un CV pour dépasser 70 % sur les ATS stricts ET souples.
                Langue de travail : {lang_label}.

                CV de base du candidat — source de vérité, ne pas inventer de données :
                <cv_base>
                {cv_json}
                </cv_base>

                Règles impératives :
                - Utilise UNIQUEMENT les informations du CV de base et de l'offre fournie
                - Intègre les mots-clés exacts de l'offre (technologies, méthodes, certifications)
                - Quantifie avec les chiffres déjà présents dans le CV base
                - Bullet points avec "•" pour chaque section de liste
                - Sois factuel, pas d'invention ni d'extrapolation

                Génère un JSON strict avec ces clés :
                - llm_summary : résumé professionnel 4-5 lignes ciblant l'offre
                - llm_skills : 10-12 compétences ordonnées par pertinence pour l'offre
                - llm_experience : 5-8 bullet points d'expérience avec mots-clés de l'offre
                - llm_education : formations reformulées en soulignant les aspects liés à l'offre
                - llm_certifications : certifications pertinentes pour l'offre
                - llm_projects : 3-4 projets les plus pertinents reformulés pour l'offre
                - llm_languages : niveaux de langues
                - llm_interests : centres d'intérêt (conserver sauf pertinence pour l'offre)

                Retourne UNIQUEMENT le JSON valide.
            """

    def _build_prompt_score(self) -> str:
        return """
                    Tu es un moteur ATS expert. Évalue la correspondance entre un CV personnalisé et une offre d'emploi.

                    Critères pondérés (total = 1.0) :
                    - Mots-clés techniques (0.30) : présence des technologies, outils, frameworks demandés
                    - Titre et niveau (0.20) : adéquation titre ciblé / profil / séniorité
                    - Expérience et domaine (0.25) : années, secteur, type de missions
                    - Formation et certifications (0.15) : diplômes et certifications requis
                    - Soft skills et langues (0.10) : compétences comportementales, langues requises

                    Retourne UNIQUEMENT ce JSON strict :
                    {
                    "score": <float 0.0-1.0>,
                    "details": {
                        "keywords": <float>,
                        "title_level": <float>,
                        "experience": <float>,
                        "education": <float>,
                        "soft_skills": <float>
                    },
                    "justification": "<2-3 phrases expliquant le score>",
                    "generate_documents": <true si score >= 0.70, sinon false>
                    }"""

    # ─── Méthode 1 : Extraction et structuration de l'offre ──────────────────

    def extract_and_structure_offer(self, offer_text: str) -> Dict[str, Any]:
        """
        Extrait les métadonnées structurées d'une offre texte brut (première moitié de job_offer).
        Retourne {"structured_offer": dict, "offer_text": str}.
        """
        logger.info("[M1] extract_and_structure_offer — appel Claude (%s) | offre %d chars",
                    self.model, len(offer_text))
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=[{"type": "text", "text": self.prompt_extract, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": f"Offre d'emploi :\n\n{offer_text}"}],
            )
            logger.info("[M1] tokens utilisés — input: %d | output: %d | cache_read: %d",
                        response.usage.input_tokens,
                        response.usage.output_tokens,
                        getattr(response.usage, "cache_read_input_tokens", 0))
            raw = next(b.text for b in response.content if b.type == "text")
            logger.debug("[M1] réponse brute Claude : %s", raw[:300])
            structured: Dict[str, Any] = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            structured["id"] = str(uuid_lib.uuid4())
            structured["cv_base_id"] = "cv_base_in_all_fr" if structured.get("language") == "fr" else "cv_base_in_all_en"
            logger.info("[M1] extraction OK — id=%s | langue=%s | pays=%s | titre=%s",
                        structured.get("id"), structured.get("language"),
                        structured.get("country"), structured.get("offer_title"))
            return {"structured_offer": structured, "offer_text": offer_text}
        except json.JSONDecodeError as e:
            logger.error("[M1] Échec parsing JSON Claude : %s | réponse brute : %s", e, raw[:500] if 'raw' in dir() else "N/A")
            return {}
        except Exception as e:
            logger.exception("[M1] Exception extract_and_structure_offer : %s", e)
            return {}

    # ─── Méthode 2 : Enrichissement LLM croisé avec cv_base ─────────────────

    def enrich_offer_with_cv(self, structured_offer: Dict[str, Any], offer_text: str) -> Dict[str, Any]:
        """
        Enrichit l'offre structurée avec les sections LLM croisées avec cv_base_in_all.
        Sauvegarde l'offre complète dans job_offer. Retourne l'offre complète.
        """
        language = structured_offer.get("language", "fr")
        system_prompt = self.prompt_enrich.get(language, self.prompt_enrich["fr"])
        logger.info("[M2] enrich_offer_with_cv — langue=%s | modèle=%s | max_tokens=%d",
                    language, self.model, self.max_tokens)
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": (
                    f"Offre texte complète :\n{offer_text}\n\n"
                    f"Offre structurée (première partie) :\n{json.dumps(structured_offer, ensure_ascii=False)}"
                )}],
            ) as stream:
                response = stream.get_final_message()

            logger.info("[M2] tokens utilisés — input: %d | output: %d | cache_read: %d",
                        response.usage.input_tokens,
                        response.usage.output_tokens,
                        getattr(response.usage, "cache_read_input_tokens", 0))

            raw = next(b.text for b in response.content if b.type == "text")
            logger.debug("[M2] réponse brute Claude : %s", raw[:300])

            try:
                llm_sections: Dict[str, Any] = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
            except json.JSONDecodeError as e:
                logger.error("[M2] Échec parsing JSON sections LLM : %s | extrait: %s", e, raw[:500])
                return {}

            full_offer = {**structured_offer, **llm_sections}
            sections_generees = [k for k in llm_sections if k.startswith("llm_")]
            logger.info("[M2] sections LLM générées : %s", sections_generees)

            cols = [
                "id", "cv_base_id", "language", "country", "city",
                "compagny_name", "compagny_type", "offer_title", "offer_description",
                "compagny_presentation", "llm_header", "llm_summary", "llm_skills",
                "llm_experience", "llm_education", "llm_certifications",
                "llm_projects", "llm_languages", "llm_interests",
            ]
            sql = f"INSERT OR REPLACE INTO job_offer ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))});"
            try:
                with sqlite3.connect(os.path.join(self.db_dir, "recruitment.db")) as conn:
                    conn.execute(sql, tuple(full_offer.get(c) for c in cols))
                    conn.commit()
                logger.info("[M2] job_offer sauvegardée en base → id=%s", full_offer.get("id"))
            except Exception as db_err:
                logger.error("[M2] Échec sauvegarde DB : %s", db_err)

            return full_offer
        except Exception as e:
            logger.exception("[M2] Exception enrich_offer_with_cv : %s", e)
            return {}

    # ─── Méthode 3 : Scoring ATS + génération CV/LM ──────────────────────────

    def score_and_generate(self, full_offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule le score ATS de l'offre enrichie vs cv_base.
        Si score >= 0.70 : génère CV et LM en texte et sauvegarde dans candidature_tracking.
        """
        language = full_offer.get("language", "fr")
        cv_base = self.cv_base_fr if language == "fr" else self.cv_base_en

        scoring_input = json.dumps({
            "cv_personnalise": {k: full_offer.get(k) for k in [
                "llm_header", "llm_summary", "llm_skills", "llm_experience",
                "llm_education", "llm_certifications", "llm_projects",
                "llm_languages", "llm_interests",
            ]},
            "offre": {k: full_offer.get(k) for k in [
                "offer_title", "offer_description", "compagny_type", "compagny_presentation",
            ]},
        }, ensure_ascii=False)

        logger.info("[M3] score_and_generate — langue=%s | modèle scoring=%s",
                    language, self.model_scoring)
        logger.info("[M3] taille input scoring : %d chars", len(scoring_input))
        try:
            score_resp = self.client.messages.create(
                model=self.model_scoring,
                max_tokens=512,
                system=[{"type": "text", "text": self.prompt_score, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": scoring_input}],
            )
            logger.info("[M3] tokens scoring — input: %d | output: %d",
                        score_resp.usage.input_tokens, score_resp.usage.output_tokens)

            raw_score = next(b.text for b in score_resp.content if b.type == "text")
            logger.debug("[M3] réponse scoring brute : %s", raw_score)

            try:
                score_data: Dict[str, Any] = json.loads(raw_score[raw_score.find("{"):raw_score.rfind("}") + 1])
            except json.JSONDecodeError as e:
                logger.error("[M3] Échec parsing JSON score : %s | extrait: %s", e, raw_score[:500])
                return {}

            score = float(score_data.get("score", 0.0))
            logger.info("[M3] score ATS = %.2f (%.0f %%) | generate_documents=%s",
                        score, score * 100, score_data.get("generate_documents"))
            logger.info("[M3] justification : %s", score_data.get("justification", ""))

            cv_text: Optional[str] = None
            lm_text: Optional[str] = None

            if score >= 0.70:
                lang_label = "français" if language == "fr" else "anglais"
                logger.info("[M3] score >= 70 %% — génération CV + LM en %s (modèle=%s)",
                            lang_label, self.model)
                doc_prompt = (
                    f"Génère en {lang_label} un CV complet et une lettre de motivation ATS-optimisés.\n\n"
                    f"CV de base : {json.dumps(cv_base, ensure_ascii=False)}\n"
                    f"Offre personnalisée : {json.dumps(full_offer, ensure_ascii=False)}\n\n"
                    "Retourne UNIQUEMENT ce JSON strict :\n"
                    '{"cv": "<CV complet structuré en texte>", '
                    '"lm": "<Lettre de motivation 3 paragraphes, ton professionnel>"}'
                )
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": doc_prompt}],
                ) as stream:
                    doc_resp = stream.get_final_message()

                logger.info("[M3] tokens génération docs — input: %d | output: %d",
                            doc_resp.usage.input_tokens, doc_resp.usage.output_tokens)
                raw_docs = next(b.text for b in doc_resp.content if b.type == "text")

                try:
                    docs: Dict[str, str] = json.loads(raw_docs[raw_docs.find("{"):raw_docs.rfind("}") + 1])
                    cv_text = docs.get("cv")
                    lm_text = docs.get("lm")
                    logger.info("[M3] CV généré : %d chars | LM générée : %d chars",
                                len(cv_text or ""), len(lm_text or ""))
                except json.JSONDecodeError as e:
                    logger.error("[M3] Échec parsing JSON CV/LM : %s | extrait: %s", e, raw_docs[:500])
            else:
                logger.info("[M3] score < 70 %% — aucun document généré")

            candidature_id = str(uuid_lib.uuid4())
            try:
                with sqlite3.connect(os.path.join(self.db_dir, "recruitment.db")) as conn:
                    conn.execute(
                        "INSERT INTO candidature_tracking (id, job_offer_id, cv, lm, matching_score) VALUES (?, ?, ?, ?, ?);",
                        (candidature_id, full_offer.get("id"), cv_text, lm_text, score),
                    )
                    conn.commit()
                logger.info("[M3] candidature_tracking sauvegardée → id=%s | score=%.2f",
                            candidature_id, score)
            except Exception as db_err:
                logger.error("[M3] Échec sauvegarde candidature_tracking : %s", db_err)

            return {
                "candidature_id": candidature_id,
                "job_offer_id": full_offer.get("id"),
                "score": score,
                "score_details": score_data.get("details"),
                "justification": score_data.get("justification"),
                "documents_generated": score >= 0.70,
                "cv": cv_text,
                "lm": lm_text,
            }
        except Exception as e:
            logger.exception("[M3] Exception score_and_generate : %s", e)
            return {}

    # ─── Envoi email via n8n ──────────────────────────────────────────────────

    def send_n8n_email(self, to_email: str, subject: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Déclenche un workflow n8n pour envoyer un email ou surveiller une réponse."""
        if not self.n8n_webhook_url:
            logger.warning("n8n_webhook_url non configuré")
            return False
        try:
            payload = {"to": to_email, "subject": subject, "content": content, **(metadata or {})}
            resp = http_requests.post(self.n8n_webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Email déclenché via n8n → {to_email}")
            return True
        except Exception as e:
            logger.error(f"Erreur send_n8n_email : {e}")
            return False
