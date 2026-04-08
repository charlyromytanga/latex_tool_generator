import spacy
from typing import Dict, Any, List, Optional

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

