#!/bin/bash
# FR : Script pour lancer les tests unitaires en local
# EN: Script to run unit tests locally

set -e

# Active l'environnement virtuel local si présent
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

pytest tests/
