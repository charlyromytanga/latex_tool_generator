# Feuille de route : Remplacement OpenAI par spaCy & Hugging Face

## 1. Analyse de l’architecture existante
- Orchestration : Extraction d’informations via OpenAI (`llm_offer_extractor.py`), fallback markdown parser.
- API : FastAPI, routes pour ingestion/offres.
- App : Consomme l’API pour afficher/traiter les offres.

---

## 2. Étapes de migration

### Étape 1 : Préparer l’environnement
- Ajouter à `requirements.txt` :
  - `spacy`
  - `fr_core_news_md`
  - `transformers`
  - `sentence-transformers`
  - `torch`
- Installer les modèles spaCy :
  ```sh
  python -m spacy download fr_core_news_md
  ```

### Étape 2 : Extraction d’informations (entités) avec spaCy
- Créer `src/orchestration/spacy_offer_extractor.py` : fonction pour extraire entreprise, lieu, poste, etc.
- Modifier l’orchestrateur pour utiliser spaCy à la place d’OpenAI.

### Étape 3 : Extraction de mots-clés avec Hugging Face
- Créer `src/orchestration/keywords_extractor.py` : fonction pour extraire les mots-clés importants.
- Appeler ce module dans l’orchestrateur après l’extraction d’entités.

### Étape 4 : Matching sémantique avec Sentence Transformers
- Créer `src/orchestration/matching.py` : encodeur + similarité cosinus.
- Utiliser ce module dans les routes de matching de l’API.

### Étape 5 : Refactorisation de l’orchestration
- Dans `ingest.py` et orchestrateurs :
  - Remplacer l’appel à OpenAI par spaCy/HF.
  - Garder le fallback markdown parser si besoin.

### Étape 6 : Mise à jour de l’API
- Les routes `/api/offers` et autres appellent les nouveaux modules d’extraction/matching.
- Les réponses incluent entités, mots-clés, scores de matching.

### Étape 7 : Consommation par l’application
- L’application consomme l’API comme avant, mais les résultats proviennent désormais de modules locaux.

### Étape 8 : Tests et validation
- Ajouter des tests unitaires pour chaque module d’extraction/matching.
- Vérifier la qualité sur des exemples réels.

---


## 4. Conseils
- Commencer par l’extraction d’entités (spaCy), puis ajouter les mots-clés, puis le matching.
- Garder le fallback markdown parser pour les cas non couverts.
- Documenter chaque étape pour faciliter la maintenance.
