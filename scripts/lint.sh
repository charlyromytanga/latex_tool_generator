#!/bin/bash
# FR : Script pour lancer pylint sur le code source
# EN: Script to run pylint on the source code

set -e

# Active l'environnement virtuel local si présent
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Lint sur src/ et tests/
pylint src/ tests/
