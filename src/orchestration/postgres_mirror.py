"""Mirror the local SQLite database into PostgreSQL.

This utility is meant as a migration bridge: SQLite remains the source of truth
for now, and PostgreSQL can be initialized and refreshed locally or on Render.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import psycopg
from psycopg import sql


TABLE_ORDER: tuple[str, ...] = (
    "offers_raw",
    "offer_keywords",
    "my_experiences",
    "my_projects",
    "formations",
    "formation_matching_scores",
    "matching_scores",
    "generations",
    "archive_manifest",
)


@dataclass(frozen=True)
class MirrorConfig:
    sqlite_path: Path
    postgres_dsn: str
    postgres_schema_path: Path
    truncate_first: bool
    init_schema: bool
    verify_counts: bool


def _read_sqlite_table(conn: sqlite3.Connection, table_name: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    columns = [column_info[1] for column_info in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    values = [tuple(row[column] for column in columns) for row in rows]
    return columns, values


def _truncate_postgres_tables(conn: psycopg.Connection[Any]) -> None:
    query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(sql.Identifier(table_name) for table_name in reversed(TABLE_ORDER))
    )
    with conn.cursor() as cur:
        cur.execute(query)


def _copy_table(
    sqlite_conn: sqlite3.Connection,
    postgres_conn: psycopg.Connection[Any],
    table_name: str,
) -> int:
    columns, rows = _read_sqlite_table(sqlite_conn, table_name)
    if not rows:
        return 0

    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    with postgres_conn.cursor() as cur:
        cur.executemany(insert_sql, rows)
    return len(rows)


def _verify_counts(sqlite_conn: sqlite3.Connection, postgres_conn: psycopg.Connection[Any]) -> None:
    for table_name in TABLE_ORDER:
        sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        with postgres_conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {} ").format(sql.Identifier(table_name)))
            postgres_count = cur.fetchone()[0]
        if sqlite_count != postgres_count:
            raise RuntimeError(
                f"Count mismatch for {table_name}: sqlite={sqlite_count} postgres={postgres_count}"
            )


def run_mirror(config: MirrorConfig) -> None:
    if not config.sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {config.sqlite_path}")
    if config.init_schema and not config.postgres_schema_path.exists():
        raise FileNotFoundError(f"PostgreSQL schema file not found: {config.postgres_schema_path}")

    sqlite_conn = sqlite3.connect(config.sqlite_path)
    try:
        with psycopg.connect(config.postgres_dsn, autocommit=False) as postgres_conn:
            if config.init_schema:
                postgres_conn.execute(config.postgres_schema_path.read_text(encoding="utf-8"))

            if config.truncate_first:
                _truncate_postgres_tables(postgres_conn)

            copied_counts: dict[str, int] = {}
            for table_name in TABLE_ORDER:
                copied_counts[table_name] = _copy_table(sqlite_conn, postgres_conn, table_name)

            if config.verify_counts:
                _verify_counts(sqlite_conn, postgres_conn)

            postgres_conn.commit()

        summary = ", ".join(f"{name}={count}" for name, count in copied_counts.items())
        print(f"[postgres-mirror] Mirror completed: {summary}")
    finally:
        sqlite_conn.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mirror the local SQLite DB into PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=Path("db/recruitment_assistant.db"),
        help="Path to the source SQLite database",
    )
    parser.add_argument(
        "--postgres-dsn",
        required=True,
        help="PostgreSQL DSN, for example postgresql://user:pass@localhost:5432/recruitment_assistant",
    )
    parser.add_argument(
        "--postgres-schema-path",
        type=Path,
        default=Path("db/schema_postgres.sql"),
        help="Path to the PostgreSQL schema file",
    )
    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Do not truncate PostgreSQL tables before copying data",
    )
    parser.add_argument(
        "--skip-init-schema",
        action="store_true",
        help="Do not apply the PostgreSQL schema before mirroring",
    )
    parser.add_argument(
        "--skip-verify-counts",
        action="store_true",
        help="Do not verify row counts after the mirror",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    run_mirror(
        MirrorConfig(
            sqlite_path=args.sqlite_path,
            postgres_dsn=args.postgres_dsn,
            postgres_schema_path=args.postgres_schema_path,
            truncate_first=not args.no_truncate,
            init_schema=not args.skip_init_schema,
            verify_counts=not args.skip_verify_counts,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())