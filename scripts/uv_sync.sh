#!/bin/bash
# FR : Script pour installer toutes les dépendances et générer le fichier uv.lock
# EN: Script to install all dependencies and generate the uv.lock file

set -e

uv sync "$@"

echo "[INFO] Dépendances installées et uv.lock généré."
