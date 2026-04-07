#!/bin/bash
# scan_secrets.sh : Recherche de secrets (clés API, tokens, etc.) dans l'historique git
# Usage : ./scripts/scan_secrets.sh

set -e

# Expressions régulières de détection (ajoutez-en si besoin)
PATTERNS=(
    'sk-[A-Za-z0-9]{20,}'           # OpenAI key
    'ghp_[A-Za-z0-9]{36,}'          # GitHub token
    'AIza[0-9A-Za-z\-_]{35}'       # Google API key
    'AKIA[0-9A-Z]{16}'              # AWS key
    'SECRET|TOKEN|PASSWORD|API_KEY' # Mots-clés génériques
)

found=0
for pattern in "${PATTERNS[@]}"; do
    echo "Recherche : $pattern"
    git log -p -G "$pattern" || true
    if git log -p -G "$pattern" | grep -qE "$pattern"; then
        found=1
    fi
done

if [ $found -eq 0 ]; then
    echo "✅ Aucun secret détecté dans l'historique git."
else
    echo "❌ Attention : des secrets potentiels ont été trouvés dans l'historique !"
    exit 1
fi
