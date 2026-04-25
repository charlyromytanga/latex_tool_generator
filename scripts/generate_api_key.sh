#!/usr/bin/env bash
# Génère une clé API robuste (SHA-256 sur 64 octets aléatoires)
# et l'injecte dans .env sans écraser les autres variables.

set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
KEY=$(head -c 64 /dev/urandom | sha256sum | awk '{print $1}')

echo ""
echo "Clé générée : $KEY"
echo ""

if grep -q "^API_GATEWAY_KEY=" "$ENV_FILE" 2>/dev/null; then
    # Remplace la ligne existante
    sed -i "s|^API_GATEWAY_KEY=.*|API_GATEWAY_KEY=\"$KEY\"|" "$ENV_FILE"
    echo "✔  API_GATEWAY_KEY mise à jour dans $ENV_FILE"
else
    echo "API_GATEWAY_KEY=\"$KEY\"" >> "$ENV_FILE"
    echo "✔  API_GATEWAY_KEY ajoutée dans $ENV_FILE"
fi
