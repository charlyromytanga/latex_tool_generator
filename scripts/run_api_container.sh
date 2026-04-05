#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="latex-tool-api:latest"
CONTAINER_NAME="latex-tool-api"
HOST_PORT="${API_PORT:-8000}"
CONTAINER_PORT=8000

usage() {
  cat <<'EOF'
Usage:
  scripts/run_api_container.sh [--no-build] [--stop] [--help]

Options:
  --no-build  Skip image build step and reuse existing image.
  --stop      Stop and remove an existing container before run.
  --help      Show this help message.

Behavior:
  - Builds image from Dockerfile.api by default.
  - Runs container with .env if present.
  - Binds host port ${API_PORT:-8000} -> container 8000.
EOF
}

BUILD_IMAGE=true
STOP_CONTAINER=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      BUILD_IMAGE=false
      shift
      ;;
    --stop)
      STOP_CONTAINER=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not in PATH." >&2
  exit 1
fi

kill_port_processes() {
  local port="$1"

  # Kill non-docker process listening on port if present.
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

kill_docker_port_conflicts() {
  local port="$1"
  local ids
  ids="$(docker ps --filter "publish=${port}" --format '{{.ID}}' || true)"
  if [[ -n "${ids}" ]]; then
    echo "[api-container] Stopping containers bound to port ${port}"
    # shellcheck disable=SC2086
    docker rm -f ${ids} >/dev/null 2>&1 || true
  fi
}

if [[ "${STOP_CONTAINER}" == true ]]; then
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[api-container] Stopping existing container: ${CONTAINER_NAME}"
    docker rm -f "${CONTAINER_NAME}" >/dev/null
  fi
fi

# Always free target port before starting the API container.
kill_docker_port_conflicts "${HOST_PORT}"
kill_port_processes "${HOST_PORT}"

if [[ "${BUILD_IMAGE}" == true ]]; then
  echo "[api-container] Building image ${IMAGE_NAME} from Dockerfile.api"
  docker build -f "${ROOT_DIR}/Dockerfile.api" -t "${IMAGE_NAME}" "${ROOT_DIR}"
fi

RUN_ARGS=(
  --name "${CONTAINER_NAME}"
  --rm
  -p "${HOST_PORT}:${CONTAINER_PORT}"
)

if [[ -f "${ROOT_DIR}/.env" ]]; then
  RUN_ARGS+=(--env-file "${ROOT_DIR}/.env")
fi

echo "[api-container] Starting API container on http://localhost:${HOST_PORT}"
docker run "${RUN_ARGS[@]}" "${IMAGE_NAME}"
