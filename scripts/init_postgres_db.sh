#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSTGRES_DSN="${POSTGRES_DSN:-${DATABASE_URL:-}}"

if [[ -z "${POSTGRES_DSN}" ]]; then
  echo "ERROR: POSTGRES_DSN or DATABASE_URL must be set" >&2
  exit 1
fi

RUNNER=(python3)
if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  RUNNER=("${ROOT_DIR}/.venv/bin/python")
elif command -v uv >/dev/null 2>&1; then
  RUNNER=(uv run python)
fi

echo "[init-postgres-db] Creating cv_base / jobs / cv_applications / applications tables"
POSTGRES_DSN_ENV="${POSTGRES_DSN}" "${RUNNER[@]}" - <<'PY'
import os

db_url = os.environ["POSTGRES_DSN_ENV"].strip()
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

from flask import Flask
from shared.bd_models.models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
with app.app_context():
    db.create_all()
PY

echo "[init-postgres-db] PostgreSQL schema ready"
