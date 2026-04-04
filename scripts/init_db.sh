#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="${ROOT_DIR}/db/recruitment_assistant.db"
SCHEMA_FILE="${ROOT_DIR}/db/schema_init.sql"

if [[ ! -f "${SCHEMA_FILE}" ]]; then
  echo "ERROR: schema file not found: ${SCHEMA_FILE}" >&2
  exit 1
fi

mkdir -p "${ROOT_DIR}/db"

if command -v sqlite3 >/dev/null 2>&1; then
  echo "[init-db] Using sqlite3 CLI"
  sqlite3 "${DB_FILE}" < "${SCHEMA_FILE}"
else
  echo "[init-db] sqlite3 binary not found, using Python stdlib fallback"
  ROOT_DIR_ENV="${ROOT_DIR}" python3 - <<'PY'
import sqlite3
import os
from pathlib import Path

root = Path(os.environ["ROOT_DIR_ENV"])
db_file = root / "db" / "recruitment_assistant.db"
schema_file = root / "db" / "schema_init.sql"

conn = sqlite3.connect(db_file)
try:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_file.read_text(encoding="utf-8"))
    conn.commit()
finally:
    conn.close()
PY
fi

if command -v sqlite3 >/dev/null 2>&1; then
  echo "[init-db] Tables created:"
  sqlite3 "${DB_FILE}" ".tables"
fi

echo "[init-db] Database ready: ${DB_FILE}"
