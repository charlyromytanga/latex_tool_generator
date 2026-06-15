"""
Migre les données de la base SQLite locale vers Supabase.

Usage :
    python scripts/migrate_sqlite_to_supabase.py
    python scripts/migrate_sqlite_to_supabase.py --db backend/db/jobcv.db
    python scripts/migrate_sqlite_to_supabase.py --dry-run
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

TABLES = ["cv_base", "jobs", "cv_applications", "applications"]


def _read_sqlite(db_path: str) -> dict[str, list[dict]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    data = {}
    for table in TABLES:
        try:
            cur = conn.execute(f"SELECT * FROM {table}")
            data[table] = [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError:
            data[table] = []
    conn.close()
    return data


def _push_to_supabase(data: dict[str, list[dict]], dry_run: bool) -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url or db_url.startswith("sqlite"):
        print("ERREUR : DATABASE_URL ne pointe pas vers Supabase.")
        print("  Vérifie que ton .env contient l'URL pooler Supabase.")
        sys.exit(1)

    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    from flask import Flask
    from shared.bd_models.models import db, CVBase, Jobs, CVApplications, Applications

    MODEL_MAP = {
        "cv_base": CVBase,
        "jobs": Jobs,
        "cv_applications": CVApplications,
        "applications": Applications,
    }

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SECRET_KEY"] = "migration"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

        total_inserted = 0
        total_skipped = 0

        for table in TABLES:
            rows = data.get(table, [])
            if not rows:
                print(f"  {table}: vide — ignoré")
                continue

            model_cls = MODEL_MAP[table]
            inserted = 0
            skipped = 0

            for row in rows:
                record_id = row.get("id")
                existing = db.session.get(model_cls, record_id)
                if existing:
                    skipped += 1
                    continue
                if dry_run:
                    print(f"  [DRY-RUN] {table}: insérerait id={record_id}")
                    inserted += 1
                    continue
                obj = model_cls(**{k: v for k, v in row.items() if hasattr(model_cls, k)})
                db.session.add(obj)
                inserted += 1

            if not dry_run and inserted > 0:
                db.session.commit()

            print(f"  {table}: {inserted} insérés, {skipped} déjà présents")
            total_inserted += inserted
            total_skipped += skipped

        print(f"\nTotal : {total_inserted} insérés, {total_skipped} ignorés (déjà dans Supabase)")


def main():
    parser = argparse.ArgumentParser(description="Migre SQLite locale → Supabase")
    parser.add_argument("--db", default=str(ROOT / "backend" / "db" / "jobcv.db"),
                        help="Chemin vers jobcv.db (défaut: backend/db/jobcv.db)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche ce qui serait migré sans écrire dans Supabase")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"ERREUR : fichier SQLite introuvable : {args.db}")
        sys.exit(1)

    print(f"Source SQLite : {args.db}")
    print(f"Destination   : {os.environ.get('DATABASE_URL', '')[:60]}...")
    if args.dry_run:
        print("Mode         : DRY-RUN (aucune écriture)\n")
    else:
        print()

    data = _read_sqlite(args.db)
    for table, rows in data.items():
        print(f"  Lu {len(rows):>3} ligne(s) depuis {table}")
    print()

    _push_to_supabase(data, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
