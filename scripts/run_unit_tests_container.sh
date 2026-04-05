#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="latex-tool-tests:latest"
CONTAINER_NAME="latex-tool-tests-run"

usage() {
  cat <<'EOF'
Usage:
  scripts/run_unit_tests_container.sh [--no-build] [--keep-container] [--help]

Options:
  --no-build        Skip Docker image build step.
  --keep-container  Do not remove the container after execution.
  --help            Show this help.

Behavior:
  - Builds Docker image from Dockerfile.test by default.
  - Runs pytest tests/src_test inside the container.
  - Writes artifacts to local directories:
      test-results/
      coverage-report/
EOF
}

BUILD_IMAGE=true
REMOVE_CONTAINER=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      BUILD_IMAGE=false
      shift
      ;;
    --keep-container)
      REMOVE_CONTAINER=false
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

mkdir -p "${ROOT_DIR}/test-results" "${ROOT_DIR}/coverage-report"

if [[ "${BUILD_IMAGE}" == true ]]; then
  echo "[tests-container] Building image ${IMAGE_NAME} from Dockerfile.test"
  docker build -f "${ROOT_DIR}/Dockerfile.test" -t "${IMAGE_NAME}" "${ROOT_DIR}"
fi

RUN_FLAGS=(--name "${CONTAINER_NAME}")
if [[ "${REMOVE_CONTAINER}" == true ]]; then
  RUN_FLAGS+=(--rm)
fi

echo "[tests-container] Running unit tests in Docker container"
docker run "${RUN_FLAGS[@]}" \
  -v "${ROOT_DIR}/test-results:/app/test-results" \
  -v "${ROOT_DIR}/coverage-report:/app/coverage-report" \
  "${IMAGE_NAME}"

echo "[tests-container] Completed. Artifacts available in:"
echo "  - ${ROOT_DIR}/test-results"
echo "  - ${ROOT_DIR}/coverage-report"
