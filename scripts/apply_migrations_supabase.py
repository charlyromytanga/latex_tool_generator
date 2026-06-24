"""
Applique les migrations ALTER TABLE manquantes sur la base Supabase.

Usage :
    python scripts/apply_migrations_supabase.py
    python scripts/apply_migrations_supabase.py --dry-run
"""

import argparse
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Migrations à appliquer — chaque entrée : (table, colonne, type SQL)
# Utilise DO $$ … $$ pour ignorer si la colonne existe déjà (idempotent).
COLUMN_MIGRATIONS = [
    ("cv_base", "jobtype",      "TEXT"),
    ("cv_base", "github",       "TEXT"),
    ("cv_base", "disponibilite","TEXT"),
]


def _make_add_column_sql(table: str, column: str, col_type: str) -> str:
    return (
        f"DO $$ BEGIN\n"
        f"  IF NOT EXISTS (\n"
        f"    SELECT 1 FROM information_schema.columns\n"
        f"    WHERE table_name='{table}' AND column_name='{column}'\n"
        f"  ) THEN\n"
        f"    ALTER TABLE {table} ADD COLUMN {column} {col_type};\n"
        f"  END IF;\n"
        f"END $$;"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Applique les migrations ALTER TABLE sur Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les SQL sans les exécuter")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url or "sqlite" in db_url:
        print("ERREUR : DATABASE_URL ne pointe pas vers Supabase.")
        sys.exit(1)

    # Normalise le schéma — NE PAS décoder le %40 du mot de passe,
    # SQLAlchemy gère les caractères percent-encodés nativement.
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)

    statements = [_make_add_column_sql(t, c, ty) for t, c, ty in COLUMN_MIGRATIONS]

    if args.dry_run:
        print("=== DRY-RUN : SQL qui serait exécuté ===\n")
        for sql in statements:
            print(sql)
            print()
        return

    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)
    with engine.begin() as conn:
        for (table, column, _), sql in zip(COLUMN_MIGRATIONS, statements):
            conn.execute(text(sql))
            print(f"  ✓  {table}.{column}")

    print("\nMigrations appliquées avec succès.")


if __name__ == "__main__":
    main()
