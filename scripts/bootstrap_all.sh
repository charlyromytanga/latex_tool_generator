#!/usr/bin/env bash
# Automatisation de l'appel des orchestrateurs pour l'insertion des données

set -e

# Appel orchestrateur formations
PYTHONPATH=src python3 src/orchestration/formations_orchestrator.py --db-path db/recruitment_assistant.db --schema-path db/schema_init.sql --log-level INFO

# Appel orchestrateur expériences
PYTHONPATH=src python3 src/orchestration/experiences_orchestrator.py --db-path db/recruitment_assistant.db --schema-path db/schema_init.sql --log-level INFO

# Appel orchestrateur projets
PYTHONPATH=src python3 src/orchestration/projects_orchestrator.py --db-path db/recruitment_assistant.db --schema-path db/schema_init.sql --log-level INFO --all-json