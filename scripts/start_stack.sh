#!/usr/bin/env bash
# Démarre la stack Docker en réutilisant les images déjà construites (sans rebuild).
# Prérequis : avoir lancé scripts/build_images.sh au moins une fois.
# Usage: scripts/start_stack.sh [--detach] [--stop]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DETACH=false
STOP=false

usage() {
  cat <<'EOF'
Usage: scripts/start_stack.sh [--detach] [--stop]

Options:
  --detach  Lance les conteneurs en arrière-plan (mode daemon).
  --stop    Arrête et supprime les conteneurs de la stack.
  --help    Affiche ce message.

Prérequis: lancer scripts/build_images.sh une fois avant la première utilisation.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --detach|-d) DETACH=true; shift ;;
    --stop)      STOP=true;   shift ;;
    --help|-h)   usage; exit 0 ;;
    *) echo "Option inconnue: $1" >&2; usage; exit 1 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker est introuvable dans le PATH." >&2
  exit 1
fi

# Ports utilisés par la stack
STACK_PORTS=(8000 8501)

free_port() {
  local port="$1"

  # Tuer les conteneurs Docker qui occupent le port
  local ids
  ids="$(docker ps --filter "publish=${port}" --format '{{.ID}}' || true)"
  if [[ -n "${ids}" ]]; then
    echo "[stack] Libération port ${port} — arrêt conteneur(s) Docker conflictuels"
    # shellcheck disable=SC2086
    docker rm -f ${ids} >/dev/null 2>&1 || true
  fi

  # Tuer les processus non-Docker qui occupent le port
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -t -i ":${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      kill -9 ${pids} >/dev/null 2>&1 || true
    fi
  fi
}

# Vérifier que les images ont été construites
MISSING=()
for img in latex-tool-api:latest latex-tool-app:latest latex-tool-runner:latest; do
  if ! docker image inspect "${img}" >/dev/null 2>&1; then
    MISSING+=("${img}")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "ERROR: Images manquantes — lance d'abord scripts/build_images.sh" >&2
  for img in "${MISSING[@]}"; do
    echo "  - ${img}" >&2
  done
  exit 1
fi

if [[ "${STOP}" == true ]]; then
  echo "[stack] Arrêt de la stack..."
  docker compose -f "${ROOT_DIR}/docker-compose.yml" down
  echo "[stack] Stack arrêtée."
  exit 0
fi

# Libérer les ports avant de démarrer
for port in "${STACK_PORTS[@]}"; do
  free_port "${port}"
done

COMPOSE_ARGS=(--no-build)
if [[ "${DETACH}" == true ]]; then
  COMPOSE_ARGS+=(-d)
  echo "[stack] Démarrage en arrière-plan (sans rebuild)..."
else
  echo "[stack] Démarrage en avant-plan (sans rebuild). Ctrl+C pour arrêter."
fi

docker compose -f "${ROOT_DIR}/docker-compose.yml" up --remove-orphans "${COMPOSE_ARGS[@]}"
