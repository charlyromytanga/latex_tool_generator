#!/usr/bin/env bash
# Construit toutes les images Docker du projet une seule fois.
# Usage: scripts/build_images.sh [--no-cache]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

NO_CACHE=""
if [[ "${1:-}" == "--no-cache" ]]; then
  NO_CACHE="--no-cache"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker est introuvable dans le PATH." >&2
  exit 1
fi

echo "[build] Construction des images Docker..."
docker compose -f "${ROOT_DIR}/docker-compose.yml" build ${NO_CACHE}

echo ""
echo "[build] Images construites :"
docker images --filter "reference=latex-tool-*" --format "  {{.Repository}}:{{.Tag}}  ({{.Size}})"
echo ""
echo "[build] Terminé. Lance './scripts/start_stack.sh' pour démarrer la stack."
