"""Offer-related request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict, Any
import json
import uuid
import datetime
import numpy as np
import os
from dotenv import load_dotenv


import spacy
from typing import Dict, Any, List, Optional
from transformers import pipeline
from keybert import KeyBERT
from langdetect import detect
from typing import List, Tuple, Union, Optional
import os
from dotenv import load_dotenv

load_dotenv()




class OfferCreateRequest(BaseModel):
    """Payload minimal pour POST /api/offers."""
    offer_input: str = Field(min_length=1, description="L'offre")

class OfferDetailsResponse(BaseModel):
    offer_id: str
    score: float
    formations: list[dict] = Field(default_factory=list)
    experiences: list[dict] = Field(default_factory=list)
    projets: list[dict] = Field(default_factory=list)





# Chargement paresseux des modèles pour éviter le temps de chargement à l'import
_NLP_MODELS = {}


def get_nlp(lang: str = "fr"):
    """Charge et retourne le modèle spaCy pour la langue demandée."""
    if lang not in _NLP_MODELS:
        if lang == "fr":
            _NLP_MODELS["fr"] = spacy.load("fr_core_news_md")
        elif lang == "en":
            _NLP_MODELS["en"] = spacy.load("en_core_web_md")
        else:
            raise ValueError(f"Langue non supportée: {lang}")
    return _NLP_MODELS[lang]


def extract_entities(text: str, lang: str = "fr") -> List[Dict[str, Any]]:
    """
    Extrait les entités nommées d'un texte avec spaCy.
    Retourne une liste de dictionnaires {text, label, start, end}.
    """
    nlp = get_nlp(lang)
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

def get_keyword_pipeline():
    global _keyword_pipe
    if _keyword_pipe is None:
        # Utilise un modèle multilingue adapté à l'extraction de mots-clés
        _keyword_pipe = pipeline("feature-extraction", model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _keyword_pipe

_kw_model = None

def get_kw_model():
    global _kw_model
    if _kw_model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        _kw_model = KeyBERT(model)  # type: ignore
    return _kw_model

def extract_keywords(text: str, top_k: Optional[int] = None) -> List[str]:
    """
    Extraction naïve de mots-clés à partir d'un texte.
    (À améliorer avec un vrai algorithme d'extraction ou un modèle adapté)
    """
    model = get_kw_model()
    lang = detect(text)
    if top_k is None:
        try:
            top_k = int(os.getenv("TOP_K_KEYWORDS", 10))
        except Exception:
            top_k = 10
    keywords = model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words='french' if lang == 'fr' else 'english',
        top_n=top_k
    )
    # keywords peut être List[Tuple[str, float]] ou List[List[Tuple[str, float]]]
    # Robust handling: always return List[str]
    if not keywords:
        return []
    # Cas List[List[Tuple[str, float]]]
    if isinstance(keywords[0], list):
        flat = []
        for sublist in keywords:
            if isinstance(sublist, list):
                for kw_tuple in sublist:
                    if isinstance(kw_tuple, tuple) and len(kw_tuple) > 0:
                        flat.append(str(kw_tuple[0]))
        return flat
    # Cas List[Tuple[str, float]] ou List[str]
    result = []
    for kw in keywords:
        if isinstance(kw, tuple) and len(kw) > 0:
            result.append(str(kw[0]))
        elif isinstance(kw, str):
            result.append(kw)
    return result

# TODO : Remplacer par une vraie extraction basée sur transformers ou keyBERT



# Chargement paresseux du modèle
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    return _model


def compute_similarity(text1: str, text2: str) -> float:
    """
    Calcule la similarité sémantique entre deux textes (cosinus).
    """
    model = get_model()
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    score = float(util.pytorch_cos_sim(emb1, emb2).item())
    return score


def match_keywords_to_text(keywords: List[str], text: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """
    Retourne les mots-clés les plus proches du texte cible.
    """
    model = get_model()
    text_emb = model.encode(text, convert_to_tensor=True)
    kw_embs = model.encode(keywords, convert_to_tensor=True)
    scores = util.pytorch_cos_sim(kw_embs, text_emb).squeeze().tolist()
    pairs = list(zip(keywords, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]


def compute_matching_for_offer(database, offer_id: str, top_k: int = 5, persist: bool = False, score_threshold: float = 0.0) -> Dict[str, Any]:
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

    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    model_version = "spacy-hf-v1"

    def summarize_matches(matches):
        scores = [score for _, score in matches]
        if not scores:
            return {
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "top_keywords": []
            }
        arr = np.array(scores)
        return {
            "max": float(np.max(arr)),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "top_keywords": [kw for kw, score in matches if score >= score_threshold][:top_k]
        }

    # Matching formations
    formation_scores = []
    for f in formations:
        text = f["program"] + " " + (f["description"] or "")
        matches = match_keywords_to_text(keywords, text, top_k=top_k)
        summary = summarize_matches(matches)
        if summary["max"] >= score_threshold:
            formation_scores.append({"formation_id": f["formation_id"], **summary})
        if persist:
            sql = """
            INSERT INTO formation_matching_scores (offer_id, formation_id, match_score, reasoning, model_version, computed_at)
            VALUES (:offer_id, :formation_id, :match_score, :reasoning, :model_version, :computed_at)
            """
            database.execute(sql, {
                "offer_id": offer_id,
                "formation_id": f["formation_id"],
                "match_score": summary["max"],
                "reasoning": json.dumps(matches, ensure_ascii=True),
                "model_version": model_version,
                "computed_at": now
            })

    # Matching expériences
    experience_scores = []
    for e in experiences:
        text = e["role"] + " " + (e["description"] or "")
        matches = match_keywords_to_text(keywords, text, top_k=top_k)
        summary = summarize_matches(matches)
        if summary["max"] >= score_threshold:
            experience_scores.append({"exp_id": e["exp_id"], **summary})
        if persist:
            sql = """
            INSERT INTO matching_scores (offer_id, exp_id, match_type, match_score, reasoning, model_version, computed_at)
            VALUES (:offer_id, :exp_id, :match_type, :match_score, :reasoning, :model_version, :computed_at)
            """
            database.execute(sql, {
                "offer_id": offer_id,
                "exp_id": e["exp_id"],
                "match_type": "experience",
                "match_score": summary["max"],
                "reasoning": json.dumps(matches, ensure_ascii=True),
                "model_version": model_version,
                "computed_at": now
            })

    # Matching projets
    project_scores = []
    for p in projects:
        text = p["repo_name"] + " " + (p["description"] or "")
        matches = match_keywords_to_text(keywords, text, top_k=top_k)
        summary = summarize_matches(matches)
        if summary["max"] >= score_threshold:
            project_scores.append({"project_id": p["project_id"], **summary})
        if persist:
            sql = """
            INSERT INTO matching_scores (offer_id, project_id, match_type, match_score, reasoning, model_version, computed_at)
            VALUES (:offer_id, :project_id, :match_type, :match_score, :reasoning, :model_version, :computed_at)
            """
            database.execute(sql, {
                "offer_id": offer_id,
                "project_id": p["project_id"],
                "match_type": "project",
                "match_score": summary["max"],
                "reasoning": json.dumps(matches, ensure_ascii=True),
                "model_version": model_version,
                "computed_at": now
            })

    return {
        "offer_id": offer_id,
        "formation_scores": formation_scores,
        "experience_scores": experience_scores,
        "project_scores": project_scores
    }

