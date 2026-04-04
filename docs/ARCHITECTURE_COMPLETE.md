# Architecture Complète - Latex Tool Generator (V2)

## Vue d'ensemble

Le projet évolue vers une plateforme de **génération intelligente et multi-canaux de documentations de candidature** (CV, lettres, emails, rapports). 

L'architecture repose sur **3 niveaux d'orchestration**, une **base de données SQLite centralisée**, des **modèles LLM pour l'extraction/matching**, et une **API FastAPI** exposée via une **app Streamlit**.

---

## 1. Ingestion et Stockage Centralisé (Niveau 1)

### 1.1 Format d'entrée des offres

**Localisation:** `data/offers/`

**Format accepté:** Markdown simple, souple et lisible

```markdown
# Titre du poste

## Entreprise
Nom de l'entreprise

## Localisation
Ville, Pays

## Tier
Tier-1 / Tier-2 / Tier-3

## Description
Texte libre descriptif de l'offre.

## Responsabilités
- Responsabilité 1
- Responsabilité 2
- ...

## Compétences requises
- Compétence 1
- Compétence 2
- ...

## Qualifications
- Qualification 1
- Qualification 2

## Bénéfices
- Bénéfice 1
- ...
```

### 1.2 Pipeline Niveau 1: Transformation et Indexation

**Processus:**
1. Lecteur offre brute (Markdown)
2. Extraction sections normalisées (regex/parser simple)
3. Validation schéma offre
4. **Stockage dans DB (table `offers_raw`)** avec:
   - `offer_id` (UUID)
   - `company_name`, `location`, `country`, `tier`
   - `raw_text` (Markdown brut)
   - `sections_json` (dict {title, company, tier, responsibilities[], skills[], qualifications[]})
   - `ingestion_timestamp`
   - `source_file` (chemin offre brute)
5. **Indexation:** Création entrée dans table `offers_index`

**Responsable:** Module `src/orchestration/ingest.py`

### 1.3 Base de Données (SQLite)

**Localisation:** `db/recruitment_assistant.db`

**Tables:**

| Table | Rôle |
|-------|------|
| `offers_raw` | Stockage offres brutes + extracted sections |
| `offer_keywords` | Keywords extraits par LLM model 1 |
| `my_experiences` | Expériences personnelles (résumé) |
| `my_projects` | Projets Git personnels (README + metadata) |
| `matching_scores` | Résultats matching LLM model 2 (offre vs exp/projet) |
| `generations` | Traces CV/LM générés (links offre + artifacts) |

**Schema détaillé:** voir `docs/DATABASE_SCHEMA.md`

---

## 2. Extraction Intelligente et Matching (Niveau 2)

### 2.1 LLM Model 1: Extraction Keywords Offre

**Entrée:** Texte offre stocké en DB

**Process:**
1. Lire offre depuis `offers_raw`
2. Interroger LLM (ex. GPT-4 local ou API) pour extraire:
   - **Keywords techniques** (languages, frameworks, tools)
   - **Soft skills requis** (communication, leadership, etc.)
   - **Domain expertise** (finance, healthcare, etc.)
   - **Seniority level** (junior, mid, senior, lead)
3. Stocker extraction en table `offer_keywords` avec:
   - `offer_id`
   - `keywords_json` (structured extraction)
   - `model_version`
   - `extraction_timestamp`

**Responsable:** Module `src/orchestration/llm_extractors.py::extract_offer_keywords()`

### 2.2 LLM Model 2: Matching Offre ↔ Expérience/Projets

**Entrée:**
- Keywords offre (depuis `offer_keywords`)
- Expériences personnelles (depuis `my_experiences`)
- Projets Git (README + metadata, depuis `my_projects`)

**Process:**
1. Pour chaque expérience + projet, calculer **score de matching** avec keywords offre
2. Récolter top N matches (ex. top 5 expériences, top 5 projets)
3. Stocker résultats en table `matching_scores`:
   - `offer_id`
   - `experience_id` / `project_id`
   - `match_score` (0.0 - 1.0)
   - `reasoning` (résumé LLM du pourquoi du match)
   - `model_version`
   - `timestamp`

**Thresholds de confiance:**
- **Score >= 0.75:** Go → Niveau 3 (génération CV/LM)
- **Score 0.5 - 0.75:** Détail recommandé (revue manuelle avant Niveau 3)
- **Score < 0.5:** Pas de recommandation, user peut forcer

**Responsable:** Module `src/orchestration/llm_extractors.py::match_offer_to_profile()`

---

## 3. Génération Multi-Canaux (Niveau 3)

### 3.1 CV et Lettre de Motivation

**Processus (pour offre validée):**
1. Lire data offre + top matches depuis DB
2. Router vers **template adapté**:
   - Langue (FR/EN)
   - Tier (1/2/3) → layout/ton
   - Domain (finance, tech, etc.) → couleurs/sections
3. Remplir sections dynamiquement:
   - Résumé professionnel: adapté à l'offre
   - Expériences: top 3-5 matches avec keywords offre soulignés
   - Projets: top 2-3 matches
   - Section recherche: alignée sur objectif offre
4. Render LaTeX via **Docker + latexmk**
5. Générer PDF + stocker metadata en DB (table `generations`)

**Responsable:** Module `src/cvrepo/` (conservé + amélioré)

### 3.2 Autres Canaux (Niveau 3 avancé)

| Canal | Responsable | Sortie |
|-------|-------------|--------|
| **Lettre de remerciement** post-entretien | `src/channels/thank_you_letter.py` | `.pdf` + `.txt` |
| **Email recruteur** | `src/channels/recruiter_email.py` | `.html` + template |
| **Rapport projet détaillé** | `src/channels/project_report.py` | `.pdf` multisection |
| **Mémoire soutenance** | `src/channels/thesis.py` | `.pdf` structuré |

---

## 4. Architecture Fichiers et Répertoires

```
.
├── docs/
│   ├── ARCHITECTURE_COMPLETE.md       (ce fichier)
│   ├── DATABASE_SCHEMA.md             (schéma SQLite + requêtes exemples)
│   ├── API_SPEC.md                    (FastAPI endpoints)
│   ├── APP_STREAMLIT.md               (interface utilisateur)
│   ├── DEPLOYMENT.md                  (CI/CD, GitHub Actions, Render)
│   └── WORKFLOWS.md                   (workflows existants, mis à jour)
│
├── db/
│   ├── recruitment_assistant.db       (SQLite, créé au premier run)
│   ├── schema_init.sql                (DDL sur initialization)
│   └── migrations/                    (versions futures)
│
├── data/
│   ├── offers/                        (offres brutes en Markdown)
│   │   └── {year}/Q{x}/tier-{n}/{country}/{company}/offer.md
│   └── schemas/
│       ├── offer_input.schema.json
│       └── (autres)
│
├── src/
│   ├── cvrepo/                        (module existant, conservé)
│   │   ├── cli.py
│   │   ├── pipeline.py
│   │   ├── job_parser.py
│   │   ├── template_engine.py
│   │   ├── archive_manager.py
│   │   ├── metadata.py
│   │   ├── validation.py
│   │   └── paths.py
│   │
│   ├── orchestration/                 (NOUVEAU - orchestration Niveau 1/2/3)
│   │   ├── __init__.py
│   │   ├── ingest.py                  (Niveau 1: ingestion + DB)
│   │   ├── llm_extractors.py          (Niveau 2: LLM keywords + matching)
│   │   ├── orchestrator.py            (Pivot principal: appelle 1→2→3)
│   │   └── config.py                  (settings LLM, thresholds, etc.)
│   │
│   ├── channels/                      (NOUVEAU - canal-spécifique)
│   │   ├── __init__.py
│   │   ├── thank_you_letter.py
│   │   ├── recruiter_email.py
│   │   ├── project_report.py
│   │   ├── thesis.py
│   │   └── base.py                    (classe commune)
│   │
│   ├── app/                           (NOUVEAU - FastAPI + Streamlit)
│   │   ├── api.py                     (FastAPI app)
│   │   ├── streamlit_app.py           (Interface Streamlit)
│   │   ├── routes/
│   │   │   ├── offers.py              (POST /upload_offer, GET /offers)
│   │   │   ├── generate.py            (POST /generate_cv_letter, GET /preview)
│   │   │   └── matching.py            (GET /matching_scores)
│   │   └── models/
│   │       ├── offer.py               (Pydantic model offre)
│   │       └── generation.py          (Pydantic model résultat)
│   │
│   └── __init__.py
│
├── runs/                              (Stockage runs, en DEHORS de src)
│   ├── run_cv/
│   │   ├── {year}/
│   │   │   └── {month}/
│   │   │       ├── tier-1/
│   │   │       │   ├── {country}/
│   │   │       │   │   └── {company}/
│   │   │       │   │       ├── offer_id_link.txt       (SQLite query pour lookup offre brute)
│   │   │       │   │       ├── cv_{offer_id}.pdf
│   │   │       │   │       └── lm_{offer_id}.pdf
│   │   │       │   ├── tier-2/
│   │   │       │   └── tier-3/
│   │   │       └── ...
│   │   └── index.jsonl                (metadata global run CV)
│   │
│   ├── run_letter/
│   │   ├── {year}/{month}/tier-{n}/{country}/{company}/
│   │   │   ├── thank_you_{offer_id}.pdf
│   │   │   ├── thank_you_{offer_id}.html
│   │   │   └── ...
│   │   └── index.jsonl
│   │
│   ├── run_recruiter_email/
│   │   ├── {year}/{month}/...
│   │   └── index.jsonl
│   │
│   ├── run_project_report/
│   │   ├── {year}/{month}/...
│   │   └── index.jsonl
│   │
│   ├── run_thesis/
│   │   ├── {year}/{month}/...
│   │   └── index.jsonl
│   │
│   └── archive/                       (Archive finale: lien persistent via DB)
│       └── (pas d'arbo fixe, gérée par DB + requête SQLite)
│
├── scripts/
│   ├── monitor_db.sh                  (surveille taille DB + table counts)
│   ├── monitor_data.sh                (surveille taille data/offers/)
│   ├── init_db.sh                     (crée DB + tables)
│   ├── ingest_offers.sh               (wrapper: python ingest batch)
│   └── (autres utilitaires)
│
├── templates/
│   ├── cv/
│   │   ├── fr/
│   │   │   ├── main.tex
│   │   │   └── sections/
│   │   ├── en/
│   │   │   ├── main.tex
│   │   │   └── sections/
│   │   └── principal/
│   ├── letters/
│   │   ├── fr/
│   │   │   ├── main.tex
│   │   │   └── sections/
│   │   └── en/
│   │       ├── main.tex
│   │       └── sections/
│   └── channels/
│       ├── thank_you/
│       ├── recruiter_email/
│       ├── project_report/
│       └── thesis/
│
├── pyproject.toml
├── Makefile
├── Dockerfile                         (pour render LaTeX + LLM services)
├── docker-compose.yml                 (optionnel: orchestration services)
│
└── .github/
    └── workflows/
        ├── ci.yml                     (test, lint)
        ├── deploy-render.yml          (deploy app + API sur Render)
        └── db-backup.yml              (backup DB)
```

---

## 5. Flux Complet Bout-en-Bout

### 5.1 Timeline pour une offre

```
USER → App Streamlit
   ↓
   POST /api/offers/upload_offer
   ↓
   [Niveau 1: Ingest]
   └─→ Parse MD → Validate → Store DB (offers_raw) → Index
   ↓
   [Niveau 2: LLM Extract + Match]
   ├─→ LLM Model 1: Extract keywords de l'offre → offers_keywords
   ├─→ LLM Model 2: Match vs my_experiences + my_projects → matching_scores
   ├─→ Compute score global
   └─→ Return to UI: "Confiance: 0.78 - Recommandé (5 expériences, 2 projets match)"
   ↓
   USER review + Confirm
   ↓
   [Niveau 3: Generate]
   ├─→ POST /api/generate/cv_letter
   ├─→ Fetch offer + top matches from DB
   ├─→ Route template (FR, Tier-2, Tech domain)
   ├─→ Fill content → LaTeX → Docker render → PDF
   ├─→ Store artifact metadata in DB (generations table)
   └─→ Archive in runs/run_cv/{year}/{month}/tier-{n}/{country}/{company}
   ↓
   GET /api/preview
   ↓
   UI Display: CV + LM preview
   ↓
   USER: "Confirm candidacy" ou "Edit manually"
   ↓
   Export to file ou Submit via integration
```

### 5.2 Exécution via `src/orchestration/orchestrator.py`

```python
# Orchestrator pseudo-code
class Orchestrator:
    
    def process_offer(self, offer_path: str, force_level: int = None) -> dict:
        """
        Orchestration complète d'une offre.
        
        :param offer_path: Chemin vers offre brute (MD)
        :param force_level: Force run jusqu'au niveau X (overrides thresholds)
        :return: {status, offer_id, level_reached, scores, generation_ids, artifacts}
        """
        
        # Level 1: Ingest
        offer_id = self.ingest_offer(offer_path)
        offer_data = self.db.fetch_offer(offer_id)
        
        # Level 2: Extract + Match
        keywords = self.llm_model_1.extract(offer_data)
        matching = self.llm_model_2.match(keywords)
        score = matching['confidence']
        
        # Decision gate
        if score < 0.5 and not force_level:
            return {"status": "LOW_CONFIDENCE", "score": score}
        
        # Level 3: Generate
        cv_artifact = self.generate_cv(offer_id)
        lm_artifact = self.generate_letter(offer_id)
        
        # Archive
        self.archive_generation(offer_id, [cv_artifact, lm_artifact])
        
        return {"status": "SUCCESS", "artifacts": [...]}
```

---

## 6. API FastAPI et App Streamlit

### 6.1 Endpoints Principal

**Base URL:**
- Local: `http://localhost:8000`
- Production (Render): `https://my-recruitment-app.onrender.com`

**Endpoints clés:** (détail en `docs/API_SPEC.md`)

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `/api/health` | GET | Health check |
| `/api/offers` | POST | Ingest nouvelle offre |
| `/api/offers/{offer_id}` | GET | Fetch offre depuis DB |
| `/api/matching/{offer_id}` | GET | Résultats LLM matching |
| `/api/generate/cv_letter` | POST | Trigger génération (Level 3) |
| `/api/preview/{generation_id}` | GET | Preview CV/LM |
| `/api/integrate/submit` | POST | Submit candidacy (integration externe) |

### 6.2 Interface Streamlit

**Localisation:** `src/app/streamlit_app.py`

**Sections:**
1. **Upload Offre:** Drag-drop ou paste Markdown
2. **Analyse Offre:** Affiche extraction LLM + keywords détectés
3. **Matching:** Vue table: expériences | score | reasoning
4. **Génération:** Bouton "Generate CV & Letter" (gated par confidence threshold)
5. **Preview:** Affichage interactif CV/LM avec zoom
6. **Export/Submit:** Options download + direct submit site

---

## 7. Déploiement et CI/CD

**Plateforme:** Render (gratuit tier acceptable)

**Flux:**
1. Push sur `main` branch
2. GitHub Actions trigger:
   - Tests + lint
   - Build Docker image
   - Push à Render
3. Render deploye app + API

**Détails:** voir `docs/DEPLOYMENT.md` + `.github/workflows/deploy-render.yml`

---

## 8. Surveillance et Maintenance

### 8.1 Monitor DB

**Script:** `scripts/monitor_db.sh`

```bash
#!/bin/bash
# Affiche taille DB + breakdown par table
sqlite3 db/recruitment_assistant.db << EOF
  .mode line
  SELECT name FROM sqlite_master WHERE type='table';
  SELECT COUNT(*) FROM offers_raw;
  SELECT COUNT(*) FROM generations;
  -- ... et taille fichier total
EOF
```

### 8.2 Monitor Data

**Script:** `scripts/monitor_data.sh`

```bash
#!/bin/bash
# Affiche taille data/offers/ + fichier count
du -sh data/offers/
find data/offers -type f | wc -l
```

---

## 9. Prochaines Phases

### Phase 1 (In Progress)
- [ ] Setup structure répertoires
- [ ] Créer doc DATABASE_SCHEMA.md
- [ ] Implémenter `src/orchestration/ingest.py`
- [ ] Setup SQLite DB + migrations

### Phase 2
- [ ] Implémenter LLM extractors (Level 2)
- [ ] Intégrer LLM API (OpenAI, Claude, local)
- [ ] Validater matching logic

### Phase 3
- [ ] Améliorer `src/cvrepo/` (Level 3)
- [ ] Ajouter autres canaux
- [ ] FastAPI routes

### Phase 4
- [ ] Streamlit app
- [ ] CI/CD complet
- [ ] Déploiement Render

---

## 10. Dépendances et Outils

**Python:**
- `fastapi`, `uvicorn` (API)
- `streamlit` (UI)
- `sqlite3` (DB)
- `pydantic` (validation)
- `requests` (LLM API calls)
- (dependencies LaTeX existantes)

**Système:**
- Docker (render LaTeX + optional LLM services)
- SQLite 3.x

**Services externes:**
- OpenAI API / Claude API (ou local LLM)
- Render.com (deployment)
- GitHub (source, CI/CD)

---

## Conclusion

Cette architecture offre **modularité**, **scalabilité**, et **traçabilité** à travers une **orchestration en 3 niveaux** avec **base de données centralisée** et **API web avec UI intuitive**. Chaque canal (CV, lettre, email, etc.) reste **indépendant et extensible**, tout en partageant l'infrastructure commune.
