#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA_FILE="${ROOT_DIR}/db/schema_postgres.sql"
POSTGRES_DSN="${POSTGRES_DSN:-${DATABASE_URL:-}}"
PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -z "${POSTGRES_DSN}" ]]; then
  echo "ERROR: POSTGRES_DSN or DATABASE_URL must be set" >&2
  exit 1
fi

if [[ ! -f "${SCHEMA_FILE}" ]]; then
  echo "ERROR: PostgreSQL schema file not found: ${SCHEMA_FILE}" >&2
  exit 1
fi

if command -v psql >/dev/null 2>&1; then
  echo "[init-postgres-db] Using psql CLI"
  psql "${POSTGRES_DSN}" -v ON_ERROR_STOP=1 -f "${SCHEMA_FILE}"
else
  echo "[init-postgres-db] psql binary not found, using Python fallback"
  RUNNER=(python3)
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    RUNNER=("${ROOT_DIR}/.venv/bin/python")
  elif command -v uv >/dev/null 2>&1; then
    RUNNER=(uv run python)
  fi
  POSTGRES_DSN_ENV="${POSTGRES_DSN}" SCHEMA_FILE_ENV="${SCHEMA_FILE}" PYTHONPATH="${PYTHONPATH}" "${RUNNER[@]}" - <<'PY'
import os
from pathlib import Path

import psycopg

schema_file = Path(os.environ["SCHEMA_FILE_ENV"])
dsn = os.environ["POSTGRES_DSN_ENV"]

with psycopg.connect(dsn, autocommit=True) as conn:
    conn.execute(schema_file.read_text(encoding="utf-8"))
PY
fi

echo "[init-postgres-db] PostgreSQL schema ready"