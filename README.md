# Latex Tool Generator

Plateforme Python pour automatiser la génération de documents de candidature (CV, lettres et artefacts associés) à partir d'offres d'emploi structurées.

## Ce Que Fait Le Projet

- Ingestion d'offres (Markdown/JSON) et validation via schémas.
- Pipeline de génération de documents (templates LaTeX + rendu PDF).
- Préparation d'une architecture API + App pour exécution locale et déploiement cloud.
- Outillage CI/CD et conteneurisation Docker pour industrialiser le workflow.

## Structure Principale

- `src/cvrepo/` : logique cœur (CLI, parsing, templates, pipeline).
- `data/` : offres, schémas et données d'entrée.
- `templates/` : templates LaTeX CV/lettres.
- `runs/` : sorties générées.
- `docs/` : architecture, API, déploiement, workflows.
- `.github/workflows/` : CI/CD GitHub Actions.

## Lancer En Local

### 1) Prérequis

- Python 3.12+
- `uv` (recommandé)
- LaTeX (si rendu PDF local hors Docker)

### 2) Installation

```bash
cd /home/cytech/dev/tools/Latex_tool_generator
uv sync
source .venv/bin/activate
```

### 3) Exécuter la CLI (exemple)

```bash
uv run cvrepo --help
```

### 4) Générer un document (exemple)

```bash
uv run cvrepo generate data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md \
  --language fr \
  --kind both \
  --output-dir runs/render
```

## Lancer En Local Avec Docker Compose

```bash
cp .env.example .env
docker-compose build
docker-compose up -d
```

Accès services:

- API: http://localhost:8000
- Docs API: http://localhost:8000/docs
- App: http://localhost:8501

Logs:

```bash
docker-compose logs -f
```

Arrêt:

```bash
docker-compose down
```

## Déployer Sur Render

Deux options:

1. Déploiement via GitHub Actions (recommandé)
2. Déploiement manuel via dashboard Render

### 1) Variables/Secrets à configurer

Dans GitHub > Settings > Secrets and variables > Actions:

- `RENDER_API_KEY`
- `RENDER_SERVICE_ID_API`
- `RENDER_SERVICE_ID_APP`
- `RENDER_SERVICE_URL_API`
- `RENDER_SERVICE_URL_APP`
- `OPENAI_API_KEY` (si utilisé)
- `CLAUDE_API_KEY` (si utilisé)

### 2) Déploiement automatique

- Push sur `main`.
- Workflow `.github/workflows/deploy-render.yml` déclenché.
- Vérification healthchecks API/App après déploiement.

### 3) Déploiement manuel (alternative)

- Créer 2 services web sur Render:
  - API (FastAPI)
  - App (Streamlit)
- Reprendre les commandes de build/start documentées dans `render.yaml`.

## CI/CD

- `ci.yml`: lint, tests, build images Docker.
- `deploy-render.yml`: déploiement Render.
- `db-backup.yml`: backup régulier base de données.

## Commandes Utiles

```bash
# Tests
uv run pytest tests/ -v

# Build images
docker-compose build

# Démarrage stack
docker-compose up -d

# Monitoring data/db
bash scripts/monitor_data.sh
bash scripts/monitor_db.sh
```

## Documentation

- `docs/INDEX.md`: point d'entrée documentation.
- `docs/ARCHITECTURE_COMPLETE.md`: architecture globale.
- `docs/API_SPEC.md`: spécification API.
- `docs/DEPLOYMENT.md`: guide CI/CD et déploiement.

## Licence

MIT
