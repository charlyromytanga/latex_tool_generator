# Documentation Index - Recruitment Assistant V2

Bienvenue dans la documentation du projet **Recruitment Assistant** V2. Architecture ambitieuse pour orchestrer la génération intelligente multi-canaux de documentations de candidature.

---

## 📖 Guides Princípaux

### 1. **[ARCHITECTURE_COMPLETE.md](ARCHITECTURE_COMPLETE.md)** 🏗️
Vue d'ensemble complète du projet: 3 niveaux d'orchestration, base de données SQLite, modules LLM, et canaux de sortie.

**À lire en premier pour comprendre:**
- Structure générale du pipeline
- Flux Niveau 1 (Ingestion), Niveau 2 (LLM), Niveau 3 (Génération)
- Organisation des fichiers et répertoires

---

### 2. **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** 🗄️
Schéma complet SQLite avec table design, relations, et requêtes utiles.

**À consulter pour:**
- Créer la base de données (`db/schema_init.sql`)
- Ajouter des offres, expériences, projets
- Récupérer résultats matching et générations
- Monitoring taille DB

---

### 3. **[API_SPEC.md](API_SPEC.md)** 🔌
Spécification REST API FastAPI complète.

**Endpoints clés:**
- `POST /api/offers` - Ingester offre
- `GET /api/offers/{offer_id}` - Récupérer offre + keywords + matching
- `GET /api/matching/{offer_id}` - Résultats LLM matching
- `POST /api/generate/cv_letter` - Trigger génération CV + LM
- `GET /api/preview/{generation_id}` - Preview artefacts
- `GET /api/download/{generation_id}/{artifact_type}` - Télécharger PDF

**À utiliser pour:**
- Développer frontend (Streamlit)
- Intégrer avec systèmes externes
- Tester via curl/Postman

---

### 4. **[APP_STREAMLIT.md](APP_STREAMLIT.md)** 🎨
Spécification interface utilisateur Streamlit.

**Sections UI:**
- Upload Offre (Drag & Drop Markdown)
- Analyse Offre (Keywords extraits)
- Matching (Score + Top expériences/projets)
- Génération (CV + LM)
- Preview (Viewer PDF interactif)
- Export & Submit (Candidature)
- Settings (Configuration)

**À lire pour:**
- Comprendre UX/UI finale
- Développer componentes Streamlit
- Implémenter intégrations

---

### 5. **[DEPLOYMENT.md](DEPLOYMENT.md)** 🚀
Guide complet CI/CD et déploiement sur Render.

**Sections:**
- GitHub Actions workflows (CI, deploy, backups)
- Configuration Render (render.yaml)
- Setup initial (secrets, DB, health checks)
- Monitoring et rollback
- Alternative: SSH deployment

**À consulter pour:**
- Configurer CI/CD
- Déployer sur Render
- Setup backups automatiques
- Troubleshoot deployments

---

### 6. **[WORKFLOWS.md](WORKFLOWS.md)** (existant) 📋
Workflows CLI existants (cvrepo, pipeline).

**À consulter pour:**
- Commandes existantes
- Pipeline legacy
- Migration vers orchestration V2

---

## 🗂️ Structure des Répertoires

```
docs/                                  # 📚 Documentation (ce fichier + autres)
├── ARCHITECTURE_COMPLETE.md           # Vue d'ensemble complète
├── DATABASE_SCHEMA.md                 # Schéma SQLite + requêtes
├── API_SPEC.md                        # Specification API FastAPI
├── APP_STREAMLIT.md                   # Specification UI Streamlit
├── DEPLOYMENT.md                      # CI/CD + Render deployment
├── INDEX.md                           # Ce fichier
└── WORKFLOWS.md                       # (existant)

db/                                    # 💾 Base de données
├── recruitment_assistant.db           # SQLite DB (généré au 1er run)
├── schema_init.sql                    # DDL initialization
└── migrations/                        # Migrations futures

scripts/                               # 🔧 Utilitaires
├── monitor_db.sh                      # Monitorer taille DB + tables
├── monitor_data.sh                    # Monitorer taille data/offers/
├── init_db.sh                         # Initialiser DB (future)
└── ingest_offers.sh                   # Batch ingest offres (future)

src/                                   # 🐍 Code Python
├── cvrepo/                            # Module existant (conservé)
├── orchestration/                     # Orchestration Niveau 1/2/3 (NOUVEAU)
│   ├── ingest.py                      # Niveau 1: Ingestion + DB
│   ├── llm_extractors.py              # Niveau 2: LLM extraction + matching
│   ├── orchestrator.py                # Orchestration centrale
│   └── config.py                      # Paramètres LLM, thresholds
├── channels/                          # Canaux de sortie (NOUVEAU)
│   ├── __init__.py
│   ├── base.py                        # Classe commune
│   ├── thank_you_letter.py            # Lettres de remerciement
│   ├── recruiter_email.py             # Emails recruteurs
│   ├── project_report.py              # Rapports projects
│   └── thesis.py                      # Mémoires soutenances
└── app/                               # API + UI (NOUVEAU)
    ├── api.py                         # FastAPI app
    ├── streamlit_app.py               # Streamlit interface
    ├── routes/
    │   ├── offers.py                  # Endpoints offres
    │   ├── generate.py                # Endpoints génération
    │   └── matching.py                # Endpoints matching
    └── models/
        ├── offer.py                   # Pydantic models
        └── generation.py              # Pydantic models

runs/                                  # 📁 Sorties générées
├── run_cv/                            # CVs générés
├── run_letter/                        # Lettres post-entretien
├── run_thank_you/                     # (Alias run_letter)
├── run_recruiter_email/               # Emails
├── run_project_report/                # Rapports projects
├── run_thesis/                        # Mémoires
└── archive/                           # Archive finale

templates/                             # 📄 LaTeX templates
├── cv/
│   ├── fr/
│   ├── en/
│   └── principal/
├── letters/
│   ├── fr/
│   └── en/
└── channels/                          # Templates canaux (NOUVEAU)
    ├── thank_you/
    ├── recruiter_email/
    ├── project_report/
    └── thesis/

data/                                  # 📊 Données d'entrée
├── offers/                            # Offres brutes (Markdown)
│   └── {year}/Q{x}/tier-{n}/{country}/{company}/offer.md
└── schemas/
    ├── offer_input.schema.json        # Schéma validation offre
    └── (autres)

.github/                               # ↔️ CI/CD GitHub Actions
└── workflows/
    ├── ci.yml                         # Tests + Lint
    ├── deploy-render.yml              # Deployment automatique
    └── db-backup.yml                  # Backup DB
```

---

## 🚀 Quick Start

### Étape 1: Clone & Setup
```bash
git clone <repo>
cd Latex_tool_generator
uv sync                                # Setup environment
uv run scripts/init_db.sh              # Initialiser DB
```

### Étape 2: Ajouter données
```bash
# Ajouter expériences personnelles via API
curl -X POST http://localhost:8000/api/experiences \
  -H "Content-Type: application/json" \
  -d '{"company": "OldCorp", "role": "Lead Dev", ...}'

# Ajouter projets Git
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "my-api", "repo_url": "...", ...}'
```

### Étape 3: Uploader offre
```bash
# Via API
curl -X POST http://localhost:8000/api/offers \
  -H "Content-Type: application/json" \
  -d '{"markdown_content": "# Senior Dev\n...", ...}'

# Ou via Streamlit UI
streamlit run src/app/streamlit_app.py
```

### Étape 4: Générer CV + LM
```bash
curl -X POST http://localhost:8000/api/generate/cv_letter \
  -H "Content-Type: application/json" \
  -d '{"offer_id": "offer-123", "language": "fr", ...}'
```

### Étape 5: Download / Preview
```bash
# Preview base64
curl http://localhost:8000/api/preview/gen-123

# Ou directement dans Streamlit UI
```

---

## 📋 Checklist Implémentation

### Phase 1 (Fondations) - Partiellement réalisée
- [x] Lire [ARCHITECTURE_COMPLETE.md](ARCHITECTURE_COMPLETE.md)
- [x] Créer DB + schema (`db/schema_init.sql`)
- [x] Fusionner les migrations dans `db/migrations/001_initial_schema.sql`
- [x] Implémenter les orchestrateurs candidat:
  - `my_projects` (DB)
  - `my_experiences` (DB)
  - `formations_template` (DB + template LaTeX)
- [ ] Implémenter `src/orchestration/ingest.py` (Niveau 1 offre)
- [ ] Tests: ingestion offre brute → DB

### Phase 2 (LLM Intelligence)
- [ ] Implémenter `src/orchestration/llm_extractors.py` (Niveau 2)
- [ ] Connecter API LLM (OpenAI / Claude / local)
- [ ] Tests: extraction keywords + matching

### Phase 3 (Génération)
- [ ] Améliorer `src/cvrepo/` pour Niveau 3
- [ ] Ajouter templates canaux (`templates/channels/`)
- [ ] Implémenter `src/channels/*.py` (lettre, email, etc.)

### Phase 4 (API + UI)
- [ ] Implémenter `src/app/api.py` (FastAPI routes)
- [ ] Implémenter `src/app/streamlit_app.py` (UI)
- [ ] Tests end-to-end: offre → CV/LM preview

### Phase 5 (Deployment)
- [ ] GitHub Actions + CI/CD (`.github/workflows/`)
- [ ] Render setup + secrets
- [ ] Database backups
- [ ] Monitoring (scripts de surveillance)

Notes:
- Le socle DB et les orchestrateurs des donnees candidat sont operationnels.
- Les phases API/UI et ingestion offre restent a implementer.

---

## 🔗 Ressources & Références

**Python/Frameworks:**
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Streamlit docs](https://docs.streamlit.io/)
- [SQLite tutorial](https://www.sqlite.org/lang.html)
- [Pydantic docs](https://docs.pydantic.dev/)

**LLM/AI:**
- [OpenAI API](https://platform.openai.com/docs/)
- [Anthropic Claude](https://console.anthropic.com/docs/)
- [Ollama (local LLM)](https://ollama.ai/)

**Deployment:**
- [Render docs](https://render.com/docs)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Docker guide](https://docs.docker.com/)

**LaTeX:**
- [LaTeX Project](https://www.latex-project.org/)
- [Overleaf templates](https://www.overleaf.com/latex/templates)

---

## 💬 Questions & Support

Pour des questions spécifiques:

1. **Archite cture générale?** → Voir [ARCHITECTURE_COMPLETE.md](ARCHITECTURE_COMPLETE.md)
2. **DB queries?** → Voir [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
3. **API endpoints?** → Voir [API_SPEC.md](API_SPEC.md)
4. **UI Streamlit?** → Voir [APP_STREAMLIT.md](APP_STREAMLIT.md)
5. **Déploiement?** → Voir [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Derniere mise a jour:** 2026-04-05  
**Version:** 2.0 (Orchestration + LLM + Multi-canaux)  
**Statut:** Documentation synchronisee avec l'etat reel du code (Phase 1 partielle)
