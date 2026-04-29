#!/usr/bin/env bash
# Lancement Streamlit en local pour le développement (utilise uv)
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "[ERREUR] uv est introuvable. Installez-le via : curl -Lsf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# Synchroniser les dépendances du groupe app
uv sync --extra app

# Lancer Streamlit
uv run streamlit run src/app/entry.py --server.port=8501 --server.address=0.0.0.0
