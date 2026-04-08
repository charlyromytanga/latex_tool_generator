
from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict, Any
import json
import uuid
import datetime
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

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
    row = database.fetch_one("SELECT keywords_json FROM offer_keywords WHERE offer_id = :offer_id", {"offer_id": offer_id})
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

