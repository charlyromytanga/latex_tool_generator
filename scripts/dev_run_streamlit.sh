#!/bin/bash
# Script de lancement Streamlit local pour le développement

set -e

# Aller à la racine du projet (si lancé ailleurs)
cd "$(dirname "$0")/.."

# Activer l'environnement virtuel
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "[ERREUR] .venv introuvable. Créez-le avec 'python -m venv .venv' puis relancez ce script."
    exit 1
fi

# Installer les dépendances si besoin
pip install --upgrade pip
pip install -r src/app/requirements.txt

# Lancer Streamlit
streamlit run src/app/entry.py --server.port=8501 --server.address=0.0.0.0
