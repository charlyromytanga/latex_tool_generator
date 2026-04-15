#!/bin/bash
# FR : Script pour créer l'environnement uv (.venv) et l'activer
# EN: Script to create the uv (.venv) environment and activate it

set -e


# Suppression de l'environnement existant s'il existe
if [ -d "../.venv" ]; then
	echo "[INFO] Suppression de l'environnement .venv existant..."
	rm -rf ../.venv
fi

# Création de l'environnement local avec uv
uv venv

# Activation (pour bash/zsh)
source .venv/bin/activate

echo "[INFO] Environnement .venv créé et activé."
