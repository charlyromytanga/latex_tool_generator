#!/usr/bin/env bash
# Automatisation de l'appel des orchestrateurs pour l'insertion des données

set -e

# Répertoire racine du dépôt
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Expose REPO_ROOT to child processes (and to sudo via --preserve-env)
export REPO_ROOT

# Exporte PYTHONPATH vers la racine pour que le package `shared` soit importable
export PYTHONPATH="$REPO_ROOT"
export DATABASE_URL="sqlite:///${REPO_ROOT}/backend/db/jobcv.db"
export RECRUITMENT_DB_PATH="$REPO_ROOT/backend/db/jobcv.db"

# Appel orchestrateur cv_base
"$REPO_ROOT"/.venv/bin/python3 shared/db_orchestration/cv_base_ingestor.py --db-path backend/db/jobcv.db

# Appel orchestrateur jobs (offres)
"$REPO_ROOT"/.venv/bin/python3 shared/db_orchestration/jobs_ingestor.py --db-path backend/db/jobcv.db
