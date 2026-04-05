#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQLITE_PATH="${SQLITE_PATH:-${ROOT_DIR}/db/recruitment_assistant.db}"
POSTGRES_DSN="${POSTGRES_DSN:-${DATABASE_URL:-}}"
PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -z "${POSTGRES_DSN}" ]]; then
  echo "ERROR: POSTGRES_DSN or DATABASE_URL must be set" >&2
  exit 1
fi

if [[ ! -f "${SQLITE_PATH}" ]]; then
  echo "ERROR: SQLite database not found: ${SQLITE_PATH}" >&2
  exit 1
fi

cd "${ROOT_DIR}"
if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHONPATH="${PYTHONPATH}" "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/src/orchestration/postgres_mirror.py" \
    --sqlite-path "${SQLITE_PATH}" \
    --postgres-dsn "${POSTGRES_DSN}" \
    --postgres-schema-path "${ROOT_DIR}/db/schema_postgres.sql"
elif command -v uv >/dev/null 2>&1; then
  PYTHONPATH="${PYTHONPATH}" uv run python "${ROOT_DIR}/src/orchestration/postgres_mirror.py" \
    --sqlite-path "${SQLITE_PATH}" \
    --postgres-dsn "${POSTGRES_DSN}" \
    --postgres-schema-path "${ROOT_DIR}/db/schema_postgres.sql"
else
  PYTHONPATH="${PYTHONPATH}" python3 "${ROOT_DIR}/src/orchestration/postgres_mirror.py" \
    --sqlite-path "${SQLITE_PATH}" \
    --postgres-dsn "${POSTGRES_DSN}" \
    --postgres-schema-path "${ROOT_DIR}/db/schema_postgres.sql"
fi

echo "[mirror-sqlite-to-postgres] Mirror completed"