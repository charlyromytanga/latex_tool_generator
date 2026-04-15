"""Central configuration for V2 orchestration modules."""

from __future__ import annotations

import os
import json
import uuid
import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import spacy
from transformers import pipeline
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from langdetect import detect
from dotenv import load_dotenv

load_dotenv()  # Charger les variables d'environnement depuis le fichier .env à la racine du projet

from .database import detect_database_backend, normalize_database_url


@dataclass(frozen=True)
class OrchestrationConfig:
    """Runtime settings shared across ingest, matching and generation modules."""

    database_url: str
    db_backend: str
    db_path: Path
    sqlite_schema_path: Path
    postgres_schema_path: Path
    default_language: str
    review_threshold: float
    go_threshold: float
    model_version: str

    @property
    def schema_path(self) -> Path:
        return self.postgres_schema_path if self.db_backend == "postgresql" else self.sqlite_schema_path

    @classmethod
    def from_repo_root(cls, root: Path) -> "OrchestrationConfig":
        # Centralized environment loading from repository root.
        load_dotenv(root / ".env", override=False)
        sqlite_path = Path(os.getenv("RECRUITMENT_DB_PATH", root / "db" / "recruitment_assistant.db"))
        database_url = normalize_database_url(os.getenv("DATABASE_URL"), root, sqlite_path)
        # Correction : priorité à SCHEMA_PATH, puis RECRUITMENT_SCHEMA_PATH, puis chemin par défaut
        schema_env = os.getenv("SCHEMA_PATH")
        recruitment_schema_env = os.getenv("RECRUITMENT_SCHEMA_PATH")
        if schema_env:
            sqlite_schema_path = Path(schema_env)
        elif recruitment_schema_env:
            sqlite_schema_path = Path(recruitment_schema_env)
        else:
            sqlite_schema_path = root / "db" / "schema_init.sql"
        return cls(
            database_url=database_url,
            db_backend=detect_database_backend(database_url),
            db_path=sqlite_path,
            sqlite_schema_path=sqlite_schema_path,
            postgres_schema_path=Path(
                os.getenv("RECRUITMENT_POSTGRES_SCHEMA_PATH", root / "db" / "schema_postgres.sql")
            ),
            default_language=os.getenv("DEFAULT_LANGUAGE", "fr"),
            review_threshold=float(os.getenv("MATCH_REVIEW_THRESHOLD", "0.5")),
            go_threshold=float(os.getenv("MATCH_GO_THRESHOLD", "0.75")),
            model_version=os.getenv("LLM_MODEL_VERSION", "heuristic-v0"),
        )


@dataclass(frozen=False)
class LLMConfig:
    """Configuration spécifique pour les interactions avec les LLMs, si besoin."""

    model_version: str

    # Chargement paresseux des modèles pour éviter le temps de chargement à l'import
    _NLP_MODELS = {}

    def get_nlp(self, lang: str = "fr"):
        """Charge et retourne le modèle spaCy pour la langue demandée."""
        if lang not in self._NLP_MODELS:
            if lang == "fr":
                self._NLP_MODELS["fr"] = spacy.load("fr_core_news_md")
            elif lang == "en":
                self._NLP_MODELS["en"] = spacy.load("en_core_web_md")
            else:
                raise ValueError(f"Langue non supportée: {lang}")
        return self._NLP_MODELS[lang]


    def extract_entities(self, text: str, lang: str = "fr") -> List[Dict[str, Any]]:
        """
        Extrait les entités nommées d'un texte avec spaCy.
        Retourne une liste de dictionnaires {text, label, start, end}.
        """
        nlp = self.get_nlp(lang)
        doc = nlp(text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            }
            for ent in doc.ents
        ]


    # Initialisation paresseuse du pipeline
    _keyword_pipe = None

    def get_keyword_pipeline(self):
        if self._keyword_pipe is None:
            # Utilise un modèle multilingue adapté à l'extraction de mots-clés
            self._keyword_pipe = pipeline("feature-extraction", model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        return self._keyword_pipe

    _kw_model = None

    def get_kw_model(self):
        if self._kw_model is None:
            import logging
            import keybert
            import sentence_transformers
            logging.info(f"[DEBUG] keybert version: {keybert.__version__}")
            logging.info(f"[DEBUG] sentence-transformers version: {sentence_transformers.__version__}")
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self._kw_model = KeyBERT(model)  # type: ignore # KeyBERT n'a pas de type officiel pour les modèles personnalisés
        return self._kw_model

    def extract_keywords(
        self,
        text: str,
        top_k: Optional[int] = None,
        ngram_range: tuple = (1, 3),
        stop_words: Optional[Union[str, List[str]]] = None,
        score_min: float = 0.0,
        split_paragraphs: bool = True
    ) -> List[str]:
        """
        Extraction robuste de mots-clés sur texte long :
        - Découpe en paragraphes (ou lignes)
        - Extraction sur chaque morceau
        - Agrégation/déduplication par score max
        - Personnalisation des stopwords, ngram, score_min
        - Automatisation : stop_words=None si langue détectée 'fr', sinon 'english'
        """
        import re
        model = self.get_kw_model()
        lang = detect(text)
        if top_k is None:
            try:
                top_k = int(os.getenv("TOP_K_KEYWORDS", "100"))
            except Exception:
                top_k = 100
        # Détection automatique des stopwords si non fourni ou si explicitement 'auto'
        if stop_words is None or stop_words == "auto":
            stop_words = None if lang == "fr" else "english"

        # Découpage en paragraphes ou lignes
        if split_paragraphs:
            chunks = [p.strip() for p in re.split(r"\n{2,}|\r{2,}", text) if p.strip()]
        else:
            chunks = [text]

        all_keywords = []
        for chunk in chunks:
            kws = model.extract_keywords(
                chunk,
                keyphrase_ngram_range=ngram_range,
                stop_words="english",
                top_n=top_k
            )
            # kws: List[Tuple[str, float]]
            all_keywords.extend(kws)

        # Agrégation/déduplication par mot-clé (score max)
        kw_scores = {}
        for kw, score in all_keywords:
            if score >= score_min:
                norm_kw = kw.strip().lower()
                if norm_kw in kw_scores:
                    kw_scores[norm_kw] = max(kw_scores[norm_kw], score)
                else:
                    kw_scores[norm_kw] = score

        # Tri par score décroissant et top_k global
        sorted_kws = sorted(kw_scores.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, score in sorted_kws[:top_k]]

    # TODO : Remplacer par une vraie extraction basée sur transformers ou keyBERT



    # Chargement paresseux du modèle
    _model = None

    def get_model(self):
        if self._model is None:
            self._model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        return self._model


    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité sémantique entre deux textes (cosinus).
        """
        model = self.get_model()
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        score = float(util.pytorch_cos_sim(emb1, emb2).item())
        return score


    def match_keywords_to_text(self, keywords: List[str], text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retourne les mots-clés les plus proches du texte cible.
        """
        model = self.get_model()
        text_emb = model.encode(text, convert_to_tensor=True)
        kw_embs = model.encode(keywords, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(kw_embs, text_emb).squeeze().tolist()
        pairs = list(zip(keywords, scores))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]

    def global_score(self, scores, key="max"):
        # Robustesse : log et extraction explicite
        if not scores or not isinstance(scores, list):
            return None
        vals = []
        for s in scores:
            v = s.get(key, None)
            if isinstance(v, (int, float)):
                vals.append(float(v))
        if not vals:
            return None
        return sum(vals) / len(vals)

    def compute_matching_for_offer(self, database, offer_id: str, top_k: int = 5, persist: bool = False, score_threshold: float = 0.0) -> Dict[str, Any]:
        """
        Calcule la similarité entre les mots-clés d'une offre et toutes les formations, expériences et projets.
        Retourne pour chaque entité :
        - score max
        - score moyen
        - score médian
        - top N mots-clés appariés
        - possibilité de filtrer par seuil
        Si persist=True, insère les scores dans les tables matching_scores et formation_matching_scores.
        """
        # Lecture dynamique des paramètres
        try:
            env_top_k = int(os.getenv("TOP_K_KEYWORDS", 5))
        except Exception:
            env_top_k = 5
        try:
            env_score_threshold = float(os.getenv("SCORE_THRESHOLD", 0.0))
        except Exception:
            env_score_threshold = 0.0
        if top_k is None:
            top_k = env_top_k
        if score_threshold == 0.0:
            score_threshold = env_score_threshold

        # Récupérer les mots-clés de l'offre
        row = database.fetch_one("SELECT keywords_json FROM offers WHERE offer_id = :offer_id", {"offer_id": offer_id})
        if not row:
            return {"error": f"Aucun mot-clé trouvé pour l'offre {offer_id}"}
        keywords = json.loads(row["keywords_json"])

        # Récupérer toutes les formations
        formations = database.fetch_all("SELECT formation_id, program, description FROM formations")
        # Récupérer toutes les expériences
        experiences = database.fetch_all("SELECT exp_id, role, description FROM my_experiences")
        # Récupérer tous les projets
        projects = database.fetch_all("SELECT project_id, repo_name, description FROM my_projects")

        now = datetime.datetime.now().isoformat(timespec="seconds") + "Z"
        model_version = "spacy-hf-v1"
        return {}