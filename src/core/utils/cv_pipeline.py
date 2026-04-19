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
class IntegrationService:
    """
    Gère l'intégration avec Claude (LLM) pour la génération des sections LLM et avec n8n pour l'automatisation email.
    """
    def __init__(self, claude_api_key: str, n8n_api_key: str ):
        self.claude_api_key = claude_api_key
        self.n8n_api_key = n8n_api_key

    def generate_llm_sections(self, offer_description: str, cv_base_sections: dict) :
        """Appelle Claude pour générer les sections LLM à partir de l'offre et du CV base."""
        pass

    def send_n8n_email(self, to_email: str, subject: str, content: str):
        """Déclenche un workflow n8n pour envoyer un email ou surveiller une réponse."""
        pass
