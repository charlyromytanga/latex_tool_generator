"""Shared database access helpers for SQLite and PostgreSQL runtimes."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine


def detect_database_backend(database_url: str) -> str:
    """Return the normalized backend name for the configured database URL."""
    lowered = database_url.lower()
    if lowered.startswith("postgresql://") or lowered.startswith("postgres://"):
        return "postgresql"
    if lowered.startswith("sqlite://"):
        return "sqlite"
    raise ValueError(f"Unsupported database backend in URL: {database_url}")


def normalize_database_url(database_url: str | None, repo_root: Path, sqlite_path: Path) -> str:
    """Normalize DATABASE_URL and keep relative SQLite paths repository-scoped."""
    if not database_url:
        return f"sqlite:///{sqlite_path.resolve()}"

    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url.removeprefix('postgres://')}"

    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        raw_path = database_url.removeprefix("sqlite:///")
        if raw_path == ":memory:":
            return database_url
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            return f"sqlite:///{(repo_root / candidate).resolve()}"

    return database_url


class Database:
    """Thin SQLAlchemy wrapper exposing a stable dict-based API."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.backend = detect_database_backend(database_url)
        self.sqlite_path = self._extract_sqlite_path(database_url) if self.backend == "sqlite" else None
        self.engine = self._create_engine()

    def _create_engine(self) -> Engine:
        connect_args: dict[str, Any] = {}
        if self.backend == "sqlite":
            if self.sqlite_path is not None:
                self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            connect_args["check_same_thread"] = False
        return create_engine(self.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)

    @staticmethod
    def _extract_sqlite_path(database_url: str) -> Path:
        raw_path = database_url.removeprefix("sqlite:///")
        return Path(raw_path)

    def _configure_connection(self, connection: Connection) -> None:
        if self.backend == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys = ON;")

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        connection = self.engine.connect()
        try:
            self._configure_connection(connection)
            yield connection
        finally:
            connection.close()

    @contextmanager
    def begin(self) -> Iterator[Connection]:
        with self.engine.begin() as connection:
            self._configure_connection(connection)
            yield connection

    def fetch_one(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(text(query), params or {}).mappings().first()
            return dict(row) if row is not None else None

    def fetch_all(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(text(query), params or {}).mappings().all()
            return [dict(row) for row in rows]

    def fetch_scalar(self, query: str, params: dict[str, Any] | None = None) -> Any:
        with self.connect() as connection:
            return connection.execute(text(query), params or {}).scalar_one_or_none()

    def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        with self.begin() as connection:
            connection.execute(text(query), params or {})

    def execute_many(self, query: str, values: list[dict[str, Any]]) -> None:
        if not values:
            return
        with self.begin() as connection:
            connection.execute(text(query), values)

    def execute_script(self, script: str) -> None:
        raw_connection = self.engine.raw_connection()
        try:
            if self.backend == "sqlite":
                raw_connection.executescript(script)
            else:
                cursor = raw_connection.cursor()
                try:
                    cursor.execute(script)
                finally:
                    cursor.close()
            raw_connection.commit()
        finally:
            raw_connection.close()

    def has_table(self, table_name: str) -> bool:
        return inspect(self.engine).has_table(table_name)

    def column_names(self, table_name: str) -> set[str]:
        return {column["name"] for column in inspect(self.engine).get_columns(table_name)}

    def can_connect(self) -> bool:
        try:
            with self.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
