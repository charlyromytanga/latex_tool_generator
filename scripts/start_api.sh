#!/usr/bin/env bash
# Lance l'API FastAPI avec uvicorn.
# Usage : ./scripts/start_api.sh [--prod]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Charge .env via Python pour un parsing robuste (gère espaces, guillemets, commentaires)
if [ -f ".env" ]; then
    eval "$(python3 - <<'PYEOF'
import re, os
with open(".env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*["\']?(.*?)["\']?\s*$', line)
        if m:
            k, v = m.group(1), m.group(2)
            print(f'export {k}="{v}"')
PYEOF
    )"
fi

# Vérifie que la clé API est définie
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "⚠  ANTHROPIC_API_KEY non définie — lance d'abord : export ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

if [ -z "${API_GATEWAY_KEY:-}" ]; then
    echo "⚠  API_GATEWAY_KEY non définie — génère-la d'abord : ./scripts/generate_api_key.sh"
    exit 1
fi

# Mode prod ou dev
if [ "${1:-}" = "--prod" ]; then
    echo "▶  Lancement en mode production"
    uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8000 --workers 2
else
    echo "▶  Lancement en mode développement (reload actif)"
    uvicorn src.api_gateway.main:app --reload --port 8000
fi
