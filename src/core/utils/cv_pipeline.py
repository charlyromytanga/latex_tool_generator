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
        import logging
        logger = logging.getLogger(__name__)
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


    def cv_base_in_alls(self) -> tuple[dict[str, Any], dict[str, Any]]:
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
            self.cv_base_in_alls_fr = {}
            self.cv_base_in_alls_en = {}

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

            self.cv_base_in_alls_fr = {
                "header_fr": "\n".join(header_fr),
                "summary_fr": "\n".join([f"• {b}" for b in summary_fr]),
                "skills_fr": "\n".join([f"• {b}" for b in soft_fr + hard_fr]),
                "experience_fr": "\n".join([f"• {e.get('ats_bullet_fr', '')}" for e in experiences_fr]),
                "education_fr": "\n".join([f"• {b}" for b in formations_fr]),
                "certifications_fr": "Microsoft Data Analyst (en cours), BMC (en cours), AMF (en cours)",
                "projects_fr": "\n".join([f"• {p.get('ats_bullet_fr', '')}" for p in projects_fr]),
                "languages_fr": "Français : bilingue ; Anglais : C1 ; Allemand : B1",
                "interests_fr": "Randonnée, musique classique, cyclisme loisir, football loisir",
            }
            self.cv_base_in_alls_en = {
                "header_en": "\n".join(header_en),
                "summary_en": "\n".join([f"• {b}" for b in summary_en]),
                "skills_en": "\n".join([f"• {b}" for b in soft_en + hard_en]),
                "experience_en": "\n".join([f"• {e.get('ats_bullet_en', '')}" for e in experiences_en]),
                "education_en": "\n".join([f"• {b}" for b in formations_en]),
                "certifications_en": "Microsoft Data Analyst (in progress), BMC (in progress), AMF (in progress)",
                "projects_en": "\n".join([f"• {p.get('ats_bullet_en', '')}" for p in projects_en]),
                "languages_en": "French: bilingual; English: C1; German: B1",
                "interests_en": "Hiking, classical music, leisure cycling, leisure football",
            }

            # Dump JSON des deux CV dans le dossier dédié
            os.makedirs(self.cv_base_in_alls_dir, exist_ok=True)
            with open(os.path.join(self.cv_base_in_alls_dir, "cv_base_in_alls_fr.json"), "w", encoding="utf-8") as f_fr:
                json.dump(self.cv_base_in_alls_fr, f_fr, ensure_ascii=False, indent=2)
            with open(os.path.join(self.cv_base_in_alls_dir, "cv_base_in_alls_en.json"), "w", encoding="utf-8") as f_en:
                json.dump(self.cv_base_in_alls_en, f_en, ensure_ascii=False, indent=2)

            return self.cv_base_in_alls_fr, self.cv_base_in_alls_en
        except Exception as e:
            logger.error(f"Erreur dans cv_base_in_alls : {e}")
            return {}, {}

