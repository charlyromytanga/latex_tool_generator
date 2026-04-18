import os
import json
import re
from pprint import pprint
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional

class CV:
    def __init__(self, data_dir: str):
        self.data_dir: str = data_dir
        self.formations_dir: str = os.path.join(data_dir, 'formations')
        self.experiencies_dir: str = os.path.join(data_dir, 'experiences')
        self.projects_dir: str = os.path.join(data_dir, 'projects')

    def load_alls(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Charge toutes les formations, expériences et projets.
        Retourne :
            tuple (formations, experiencies, projects)
            - formations : list[dict[str, Any]]
            - experiencies : list[dict[str, Any]]
            - projects : list[dict[str, Any]]
        """
        import logging
        logger = logging.getLogger(__name__)
        formations_files: list[str] = [f for f in os.listdir(self.formations_dir) if f.endswith('.json')]
        experiencies_files: list[str] = [f for f in os.listdir(self.experiencies_dir) if f.endswith('.json')]
        projects_files: list[str] = [f for f in os.listdir(self.projects_dir) if f.endswith('.json')]

        formations: list[dict[str, Any]] = []
        experiencies: list[dict[str, Any]] = []
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
        for file in experiencies_files:
            try:
                with open(os.path.join(self.experiencies_dir, file), 'r', encoding='utf-8') as f:
                    data_experiencies = json.load(f)
                    if isinstance(data_experiencies, dict) and 'experiences' in data_experiencies:
                        experiencies.extend([x for x in data_experiencies['experiences'] if isinstance(x, dict)])
                    elif isinstance(data_experiencies, dict):
                        experiencies.append(data_experiencies)
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

        return formations, experiencies, projects
    
    def cv_base_in_alls(self):
        pass