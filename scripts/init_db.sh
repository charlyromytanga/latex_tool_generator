#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="${ROOT_DIR}/backend/db/jobcv.db"
SCHEMA_FILE="${ROOT_DIR}/backend/db/schema_init.sql"

if [[ ! -f "${SCHEMA_FILE}" ]]; then
  echo "ERROR: schema file not found: ${SCHEMA_FILE}" >&2
  exit 1
fi

mkdir -p "${ROOT_DIR}/backend/db"

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
db_file = root / "backend" / "db" / "jobcv.db"
schema_file = root / "backend" / "db" / "schema_init.sql"

conn = sqlite3.connect(db_file)
try:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_file.read_text(encoding="utf-8"))
    conn.commit()
finally:
    conn.close()
PY
fi

# If the database already exists, migrate the cv_base schema if needed.
if [[ -f "${DB_FILE}" ]]; then
  if ! sqlite3 "${DB_FILE}" "PRAGMA table_info(cv_base);" | awk -F'|' '{print $2}' | grep -qx "target_titles"; then
    echo "[init-db] Migrating cv_base: adding target_titles column"
    sqlite3 "${DB_FILE}" "ALTER TABLE cv_base ADD COLUMN target_titles TEXT;"
    sqlite3 "${DB_FILE}" "UPDATE cv_base SET target_titles = target_title WHERE target_titles IS NULL AND target_title IS NOT NULL;"
  fi
fi

# Ensure the database directory and file are writable by the creating user.
# If the script is run with sudo, preserve the original invoking user.
OWNER_UID="${SUDO_UID:-$(id -u)}"
OWNER_GID="${SUDO_GID:-$(id -g)}"
if [[ "${EUID}" -eq 0 ]]; then
  chown "${OWNER_UID}:${OWNER_GID}" "${DB_FILE}"
fi
chmod 664 "${DB_FILE}"
chmod 775 "$(dirname "${DB_FILE}")"

echo "[init-db] Tables created:"
sqlite3 "${DB_FILE}" ".tables"

echo "[init-db] Database ready: ${DB_FILE}"
