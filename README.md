# Plateforme de Génération Intelligente et Multi-Canaux de Documentations de Candidature

> Transformer une offre d'emploi en candidature complète et personnalisée — CV, lettre de motivation, mer emails, rapports et bien plus — grâce à une orchestration intelligente pilotée par LLM.

---

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Structure du Projet](#structure-du-projet)
- [Stack Technique](#stack-technique)
- [Commandes Utiles](#commandes-utiles)
- [Feuille de Route](#feuille-de-route)
- [Contribution](#contribution)

---

## 🎯 Vue d'Ensemble

**Latex_tool_generator** est une plateforme d'automatisation de candidature qui transforme des offres d'emploi brutes en documentations personnalisées et multi-canaux.

### Fonctionnalités Principales

- **Ingestion Intelligente** : Parse des offres Markdown, extrait les sections normalisées, stocke dans SQLite
- **Matching Intelligent** : Utilise des LLM pour extraire keywords et matcher l'offre avec vos expériences/projets
- **Génération Multi-Canaux** :
  - ✅ CV personnalisé (FR/EN)
  - ✅ Lettre de motivation (FR/EN)  
  - ✅ Lettres post-entretien
  - ✅ Emails de prospection
  - ✅ Rapports de projets détaillés
  - ✅ Préparation de mémoire/présentation

- **Interface Moderne** : Streamlit UI avec 7 onglets (upload, analyse, matching, génération, preview, export, settings)
- **API REST** : FastAPI pour intégrations tierces
- **Déploiement Cloud** : CI/CD GitHub Actions + Render.com

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone le projet
git clone <repo-url>
cd Latex_tool_generator

# Configure l'environnement Python (avec uv)
uv sync

# Ou avec venv standard
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configuration Initiale

```bash
# Initialise la base de données SQLite
python -m cvrepo.orchestration.ingest --init-db

# Charge tes expériences personnelles  
python -m cvrepo.orchestration.ingest --load-experiences path/to/experiences.json

# Charge tes projets GitHub
python -m cvrepo.orchestration.ingest --load-projects --github-user <username>
```

### 3. Upload une Offre d'Emploi

```bash
# Via CLI
python -m cvrepo.orchestration.orchestrator --offer path/to/offer.md

# Via API (si déployée)
curl -X POST http://localhost:8000/api/v1/offers/upload \
  -F "file=@offer.md"

# Via Streamlit (local)
streamlit run src/app/streamlit_app.py
```

### 4. Génère des Documentations

```bash
# CLI
python -m cvrepo.orchestration.orchestrator --generate --offer-id <id> \
  --channels cv,letter --tier 1 --language fr

# Streamlit : Tab "Génération" → Select offer → Click "Generate"
```

---

## 🏗️ Architecture

### 3-Niveaux d'Orchestration

```
┌─────────────────────────────────────────────────────┐
│ NIVEAU 1: INGESTION (Data Normalization)            │
├─────────────────────────────────────────────────────┤
│  • Parse offres Markdown                            │
│  • Extrait sections (poste, lieu, skills, etc.)     │
│  • Valide + stocke dans SQLite (offers_raw)         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ NIVEAU 2: EXTRACTION & MATCHING (AI Intelligence)   │
├─────────────────────────────────────────────────────┤
│  • LLM Model 1 : Extrait keywords (skills, domain)  │
│  • LLM Model 2 : Match offer vs expériences/projects│
│  • Génère confidence scores (0.0 → 1.0)            │
│  • Gated Decision : skip/review/go                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ NIVEAU 3: GÉNÉRATION MULTI-CANAUX (Output Rendering)│
├─────────────────────────────────────────────────────┤
│  • CV personnalisé + Lettre (LaTeX → PDF)           │
│  • Lettres post-entretien                           │
│  • Emails de prospection                            │
│  • Rapports de projets                              │
│  • Préparation mémoire                              │
│  • Archive + metadata                               │
└─────────────────────────────────────────────────────┘
```

### Flux Décisionnel

```
Offre → Niveau 1 (Ingest) → Niveau 2 (LLM Matching)
                                    ↓
                          Confidence Score
                                    ↓
                    ┌─────────────┬─────────────┐
                confidence       confidence       confidence
                < threshold      [threshold]     > threshold
                    ↓               ↓              ↓
                  SKIP           REVIEW          GO
               (archive)      (manual check)   (auto-generate)
                                                 ↓
                            Niveau 3 (Generate)
```

---

## 📚 Documentation

| Document | Descripti |
|----------|-----------|
| [📖 INDEX.md](docs/INDEX.md) | **Index maître** — Table complète, lien rapide, 5 phases implémentation |
| [🏗️ ARCHITECTURE_COMPLETE.md](docs/ARCHITECTURE_COMPLETE.md) | **Architecture détaillée** — 3 niveaux, ingestion, DB schema, canaux, API, UI, monitoring |
| [🗄️ DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | **Schéma SQLite** — DDL, relations, 7 tables, exemples requêtes, index |
| [🔌 API_SPEC.md](docs/API_SPEC.md) | **Spécification REST API** — 10+ endpoints, JSON, Render config, auth |
| [🎨 APP_STREAMLIT.md](docs/APP_STREAMLIT.md) | **Interface Streamlit** — 7 onglets, composants, UX details, responsive |
| [🚀 DEPLOYMENT.md](docs/DEPLOYMENT.md) | **CI/CD & Deployment** — GitHub Actions, Render, backup, rollback, scaling |

**Accès rapide :** Débute par [INDEX.md](docs/INDEX.md) pour une vue d'ensemble, puis consulte les docs spécialisées selon tes besoins.

---

## 📁 Structure du Projet

```
Latex_tool_generator/
├── docs/                          # Documentation complète
│   ├── INDEX.md                   # Index maître + feuille de route
│   ├── ARCHITECTURE_COMPLETE.md   # Architecture 3 niveaux
│   ├── DATABASE_SCHEMA.md         # Schema SQLite + DDL
│   ├── API_SPEC.md                # Spécification REST API
│   ├── APP_STREAMLIT.md           # Interface UI
│   ├── DEPLOYMENT.md              # CI/CD + Render deployment
│   ├── MIGRATION.md               # Existing docs (legacy)
│   ├── CLI.md                     # CLI ref (legacy)
│   └── WORKFLOWS.md               # Workflows (legacy)
│
├── src/
│   ├── cvrepo/                    # Core legacy modules (préservés)
│   │   ├── cli.py                 # CLI entry point
│   │   ├── pipeline.py            # Niveau 3: CV/Letter generation
│   │   ├── job_parser.py          # Text extraction
│   │   ├── template_engine.py     # LaTeX rendering
│   │   ├── archive_manager.py     # Archive management
│   │   ├── validation.py          # Schema validation
│   │   ├── metadata.py            # Metadata inference
│   │   └── paths.py               # Path utilities
│   │
│   ├── orchestration/             # NEW: 3-level orchestration (Phase 1-2)
│   │   ├── ingest.py              # Niveau 1: Markdown → DB
│   │   ├── llm_extractors.py      # Niveau 2: LLM Models 1 & 2
│   │   ├── orchestrator.py        # Main orchestration flow
│   │   └── config.py              # LLM settings, thresholds
│   │
│   ├── channels/                  # NEW: Multi-channel generation (Phase 3)
│   │   ├── base.py                # Abstract Channel class
│   │   ├── thank_you_letter.py    # Post-interview letters
│   │   ├── recruiter_email.py     # Outreach emails
│   │   ├── project_report.py      # Detailed project reports
│   │   └── thesis.py              # Thesis/presentation memos
│   │
│   └── app/                       # NEW: FastAPI + Streamlit (Phase 4)
│       ├── api.py                 # FastAPI application
│       ├── streamlit_app.py       # Streamlit UI
│       ├── routes/
│       │   ├── offers.py          # Offer endpoints
│       │   ├── generate.py        # Generation endpoints
│       │   └── matching.py        # Matching results endpoints
│       └── models/
│           ├── offer.py           # Offer Pydantic models
│           └── generation.py      # Generation Pydantic models
│
├── db/                            # NEW: Database management (Phase 1)
│   ├── schema_init.sql            # SQLite schema definition
│   ├── migrations/                # Future: Alembic migrations
│   └── recruitment_assistant.db   # SQLite database file (generated)
│
├── templates/
│   ├── cv/                        # Existing CV templates (preserved)
│   │   ├── fr/sections/           # French CV sections (legacy)
│   │   ├── en/sections/           # English CV sections (legacy)
│   │   └── principal/             # Master templates
│   ├── letters/                   # Existing letter templates (preserved)
│   │   ├── fr/main.tex            # French letter template
│   │   └── en/main.tex            # English letter template
│   └── channels/                  # NEW: Multi-channel templates (Phase 3)
│       ├── thank_you/             # Thank-you letter templates
│       ├── recruiter_email/       # Email templates
│       ├── project_report/        # Report templates
│       └── thesis/                # Thesis templates
│
├── runs/                          # Output directories per channel
│   ├── run_cv/                    # Generated CVs
│   ├── run_letter/                # Generated letters
│   ├── run_thank_you/             # Thank-you letters
│   ├── run_recruiter_email/       # Outreach emails
│   ├── run_project_report/        # Project reports
│   ├── run_thesis/                # Thesis outputs
│   └── archive/                   # Final archive (existing)
│       └── index.jsonl            # Archive manifest
│
├── data/
│   ├── offers/                    # Raw and processed offers
│   │   ├── 2026/Q1/tier-{1,2,3}/ # Tier-based organization
│   │   └── README.md
│   ├── archive/                   # Legacy archive
│   └── schemas/
│       ├── artifact.schema.json   # Artifact validation schema
│       └── job_offer.schema.json  # Offer validation schema
│
├── scripts/
│   ├── monitor_db.sh              # Monitor SQLite database size/table counts
│   ├── monitor_data.sh            # Monitor data/ directory usage
│   ├── Clean.sh                   # Clean temporary files (existing)
│   └── README.md                  # Scripts documentation
│
├── tests/
│   ├── test_archive_manager.py
│   ├── test_job_parser.py
│   ├── test_metadata_index.py
│   ├── test_pipeline.py
│   ├── test_validation.py
│   └── __pycache__/
│
├── .github/workflows/             # NEW: CI/CD workflows (Phase 5)
│   ├── ci.yml                     # Test & lint workflow
│   ├── deploy-render.yml          # Deploy to Render.com
│   └── db-backup.yml              # Database backup workflow
│
├── Dockerfile                     # Docker for LaTeX isolation (existing)
├── Makefile                       # Build commands
├── pyproject.toml                 # Poetry/pip-tools configuration
├── README.md                      # THIS FILE
├── .gitignore
└── .venv/                         # Python virtual environment (uv)
```

**Légende :**
- `NEW:` = Créé dans cette refonte
- `(Phase X)` = Ajout implémentation en phase X
- `(preserved)` = Conservé de l'architecture précédente
- `(existing)` = Fichiers déjà présents

---

## 🛠️ Stack Technique

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Core application |
| **Package Mgr** | `uv` | Fast dependency management |
| **Database** | SQLite 3.x | Central data storage (7 tables, normalized) |
| **API** | FastAPI + Uvicorn | REST endpoints, async rendering |
| **UI** | Streamlit | Interactive web interface (7 tabs) |
| **Document Gen** | LaTeX + latexmk | PDF rendering (existing) |
| **AI/LLM** | OpenAI/Claude API or Ollama | Extraction & matching models |
| **Validation** | Pydantic v2+ | Data models & schema validation |
| **Containerization** | Docker | LaTeX render isolation |
| **CI/CD** | GitHub Actions | Test, lint, deploy pipelines |
| **Deployment** | Render.com | Cloud hosting + database backups |
| **Version Control** | Git + GitHub | Source code management |

---

## ⚙️ Commandes Utiles

### Développement Local

```bash
# Activate environment
source .venv/bin/activate

# Install dependencies (avec uv)
uv sync

# Run tests
pytest tests/ -v

# Run linters
pylint src/ --disable=all --enable=E,F
black src/ --check

# Format code
black src/ tests/
```

### Database Management

```bash
# Initialiser la base de données
python -m cvrepo.orchestration.ingest --init-db

# Charger expériences personnelles
python -m cvrepo.orchestration.ingest --load-experiences data/my_experiences.json

# Monitor database size & table counts
bash scripts/monitor_db.sh

# Monitor data directories usage
bash scripts/monitor_data.sh
```

### API & UI (Local)

```bash
# Démarrer API (localhost:8000)
python -m uvicorn src.app.api:app --reload

# Démarrer Streamlit UI (localhost:8501)
streamlit run src/app/streamlit_app.py

# Tester un endpoint
curl http://localhost:8000/api/v1/health
```

### CLI (Legacy - Maintained)

```bash
# Generate CV from offer
python -m cvrepo --input path/to/offer.md --output runs/run_cv/

# Archive with metadata
python -m cvrepo --archive --tier 1 --language fr
```

### Docker (LaTeX Rendering)

```bash
# Build LaTeX container
docker build -t latex-renderer .

# Render PDF from template
docker run --rm -v $(pwd)/templates:/templates \
  latex-renderer pdflatex -synctex=1 -interaction=nonstopmode /templates/main.tex
```

---

## 📋 Feuille de Route (5 Phases)

### Phase 1 : Fondations (Semaines 1-2)
- [ ] Initialiser SQLite database avec 7 tables
- [ ] Implémenter `src/orchestration/ingest.py` (Niveau 1)
- [ ] Parser Markdown offers → normalized storage
- [ ] Écrire tests unitaires pour ingestion
- [ ] Documenter format Markdown attendu

### Phase 2 : Intelligence LLM (Semaines 3-4)
- [ ] Implémenter `src/orchestration/llm_extractors.py` (Niveau 2)
- [ ] Intégrer LLM API (OpenAI/Claude/Ollama)
- [ ] Model 1: Keyword extraction + storage
- [ ] Model 2: Experience/project matching + scoring
- [ ] Implémenter gated decision flow (threshold-based)
- [ ] Écrire tests + prompts examples

### Phase 3 : Multi-Canaux (Semaines 5-6)
- [ ] Implémenter `src/channels/base.py` + subclasses
- [ ] Thank-you letters + Recruiter emails
- [ ] Project reports + Thesis memos
- [ ] Refactor `pipeline.py` → Niveau 3
- [ ] Créer templates pour chaque canal (FR/EN)
- [ ] Tester LaTeX rendering par canal

### Phase 4 : API & UI (Semaines 7-8)
- [ ] Implémenter FastAPI (`src/app/api.py`) avec 10 endpoints
- [ ] Implémenter Streamlit UI (`src/app/streamlit_app.py`)
- [ ] Intégrer orchestrator.py dans routes
- [ ] PDF preview + file download
- [ ] Settings customization (thresholds, language, LLM config)
- [ ] End-to-end testing (upload → generate → archive)

### Phase 5 : Déploiement (Semaines 9-10)
- [ ] Créer GitHub Actions workflows (.ci.yml, deploy-render.yml, db-backup.yml)
- [ ] Configurer Render service (FastAPI + Streamlit)
- [ ] Setup secrets (API keys, database URL)
- [ ] Test database backups + rollback procedure
- [ ] Performance scaling (Pro vs. Standard tier)
- [ ] Production monitoring + logging

**Détail complet :** Voir [INDEX.md](docs/INDEX.md#feuille-de-route).

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v --cov=src/cvrepo --cov=src/orchestration --cov=src/channels --cov=src/app

# Run specific test file
pytest tests/test_job_parser.py -v

# Run with specific marker (future)
pytest -m "not integration" -v
```

Les tests complets seront implémentés après Phase 1. Voir [INDEX.md](docs/INDEX.md#strategy-de-test).

---

## 🔧 Monitoring & Maintenance

### Database Health Check

```bash
bash scripts/monitor_db.sh
```

Fournit :
- Taille SQLite totale
- Row counts par table
- Archive summary
- Threshold breach alerts

### Data Directory Monitoring

```bash
bash scripts/monitor_data.sh
```

Fournit :
- Taille data/offers/ par tier/year/country
- Top 10 fichiers volumineux
- Recommandations de cleanup

---

## 📖 Contribution

### Code Style

- **Format:** Black (80 chars)
- **Linting:** Pylint (E, F)
- **Type Hints:** Pydantic v2+, Python 3.11+ type annotations
- **Docstrings:** Google style (functions, classes)

### Branch Convention

- `feat/`: Feature branches (ex: `feat/level2-llm-matching`)
- `fix/`: Bug fixes
- `docs/`: Documentation updates
- `chore/`: Configuration, dependencies

### PR Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code formatted (`black src/`)
- [ ] No linting errors (`pylint src/ --disable=all --enable=E,F`)
- [ ] Documentation updated (docstrings, README)
- [ ] Linked to issue/task (if applicable)

---

## 📝 License

MIT License — Voir LICENSE file.

---

## 📧 Contact & Support

Pour questions, issues ou suggestions :
- 📋 Ouvre une issue GitHub
- 💬 Crée une discussion
- 📬 Contacte l'équipe maintainers

---

## 🎯 Key Insights

> **"De l'offre brute au PDF candidature en une orchestration intelligente."**

Cette plateforme transforme le processus de candidature en 3 étapes :

1. **Niveau 1** : Normalisation des données
2. **Niveau 2** : Intelligence artificielle
3. **Niveau 3** : Génération multi-canaux

Résultat : Une candidature personnalisée, complète et prête à soumettre en minutes, pas heures.

---

**Last Updated:** April 5, 2026  
**Version:** 0.1.0 (Architecture Phase)  
**Status:** 🟡 Documentation complete, Implementation pending (Phase 1 starts here)

Pour commencer → [Lis INDEX.md](docs/INDEX.md) | [Consulte ARCHITECTURE_COMPLETE.md](docs/ARCHITECTURE_COMPLETE.md) | [Vérife DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
