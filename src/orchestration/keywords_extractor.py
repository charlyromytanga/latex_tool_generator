from transformers import pipeline
from keybert import KeyBERT
from langdetect import detect
from typing import List, Tuple, Union, Optional
import os
from dotenv import load_dotenv

load_dotenv()

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
