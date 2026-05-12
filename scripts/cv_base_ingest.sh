#!/usr/bin/env bash
# cv_base_ingest.sh
# -----------------
# Lance l'ingestion cv_base depuis docs/cv_base/*.json vers jobcv.db.
#
# Usage :
#   ./scripts/cv_base_ingest.sh                        # ingère tous les fichiers
#   ./scripts/cv_base_ingest.sh docs/cv_base/cv_base_fr.json   # ingère un seul fichier
#   ./scripts/cv_base_ingest.sh --db-path /custom/path/jobcv.db
#
# Les enregistrements existants sont supprimés puis réinsérés (replace).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

python -m shared.db_orchestration.cv_base_ingestor "$@"
