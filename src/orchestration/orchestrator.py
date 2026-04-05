"""Project bootstrap orchestration.

This module reads repository metadata from the README on a target git branch
using a Docker container, then persists parsed data into the `my_projects`
SQLite table.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence
from uuid import uuid4


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectRecord:
    """Data payload persisted into my_projects."""

    repo_name: str
    repo_url: str
    description: str
    languages: list[str]
    technologies: list[str]
    readme_full_text: str
    stars: int | None = None
    last_updated: str | None = None


class DockerGitRepositoryReader:
    """Reads README content from a local git repo using an isolated container."""

    def __init__(
        self,
        repo_path: Path,
        branch: str = "main",
        docker_image: str = "alpine/git:latest",
    ) -> None:
        self.repo_path = repo_path.resolve()
        self.branch = branch
        self.docker_image = docker_image

    def read_readme_from_branch(self) -> str:
        """Clone local repository in a container, checkout branch, and return README."""
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")

        LOGGER.info("Reading README via container from branch '%s'", self.branch)

        script = (
            "set -e; "
            "git config --global --add safe.directory /source; "
            "git config --global --add safe.directory /source/.git; "
            'tmp_dir="$(mktemp -d)"; '
            "git clone /source \"$tmp_dir/repo\"; "
            "cd \"$tmp_dir/repo\"; "
            "git checkout \"$TARGET_BRANCH\" >/dev/null || "
            "git checkout -B \"$TARGET_BRANCH\" \"origin/$TARGET_BRANCH\" >/dev/null; "
            "if [ ! -f README.md ]; then echo 'README.md not found on selected branch' >&2; exit 10; fi; "
            "cat README.md"
        )

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--entrypoint",
            "sh",
            "-e",
            f"TARGET_BRANCH={self.branch}",
            "-v",
            f"{self.repo_path}:/source:ro",
            self.docker_image,
            "-lc",
            script,
        ]

        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Docker command timed out while reading README") from exc
        except OSError as exc:
            raise RuntimeError("Failed to execute Docker command") from exc

        if result.returncode != 0:
            stderr = result.stderr.strip() or "No stderr output"
            raise RuntimeError(f"Container read failed (exit={result.returncode}): {stderr}")

        readme = result.stdout.strip()
        if not readme:
            raise RuntimeError("README read succeeded but content is empty")

        return readme


class ReadmeProjectParser:
    """Parses README text into project metadata for my_projects."""

    LANGUAGE_KEYWORDS = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "java": "Java",
        "c++": "C++",
        "c#": "C#",
        "go": "Go",
        "rust": "Rust",
        "sql": "SQL",
        "latex": "LaTeX",
    }

    TECHNOLOGY_KEYWORDS = {
        "fastapi": "FastAPI",
        "streamlit": "Streamlit",
        "docker": "Docker",
        "github actions": "GitHub Actions",
        "sqlite": "SQLite",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "latex": "LaTeX",
        "render": "Render",
    }

    def parse(self, readme_text: str) -> tuple[str, list[str], list[str]]:
        """Extract description, languages, and technologies from README text."""
        clean_lines = [line.strip() for line in readme_text.splitlines() if line.strip()]

        description = "Project documentation"
        for line in clean_lines:
            if line.startswith("#"):
                continue
            description = line[:500]
            break

        lower = readme_text.lower()
        languages = self._extract_matches(lower, self.LANGUAGE_KEYWORDS)
        technologies = self._extract_matches(lower, self.TECHNOLOGY_KEYWORDS)

        return description, languages, technologies

    @staticmethod
    def _extract_matches(content: str, mapping: dict[str, str]) -> list[str]:
        values: list[str] = []
        for keyword, label in mapping.items():
            if keyword in content:
                values.append(label)
        return sorted(set(values))


class ProjectRepositoryGateway:
    """Database gateway for the my_projects table."""

    def __init__(self, db_path: Path, schema_path: Path) -> None:
        self.db_path = db_path.resolve()
        self.schema_path = schema_path.resolve()

    def ensure_schema(self) -> None:
        """Create schema from file if my_projects table is missing."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='my_projects'"
            ).fetchone()

            if table_exists:
                return

            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

            LOGGER.info("my_projects missing, initializing schema from %s", self.schema_path)
            conn.executescript(self.schema_path.read_text(encoding="utf-8"))
            conn.commit()

    def upsert_project(self, project: ProjectRecord) -> None:
        """Insert or update one project record in my_projects."""
        payload = {
            "project_id": str(uuid4()),
            "repo_name": project.repo_name,
            "repo_url": project.repo_url,
            "description": project.description,
            "languages_json": json.dumps(project.languages, ensure_ascii=True),
            "technologies_json": json.dumps(project.technologies, ensure_ascii=True),
            "readme_full_text": project.readme_full_text,
            "stars": project.stars,
            "last_updated": project.last_updated,
        }

        sql = """
        INSERT INTO my_projects (
            project_id,
            repo_name,
            repo_url,
            description,
            languages_json,
            technologies_json,
            readme_full_text,
            stars,
            last_updated
        ) VALUES (
            :project_id,
            :repo_name,
            :repo_url,
            :description,
            :languages_json,
            :technologies_json,
            :readme_full_text,
            :stars,
            :last_updated
        )
        ON CONFLICT(repo_name) DO UPDATE SET
            repo_url = excluded.repo_url,
            description = excluded.description,
            languages_json = excluded.languages_json,
            technologies_json = excluded.technologies_json,
            readme_full_text = excluded.readme_full_text,
            stars = excluded.stars,
            last_updated = excluded.last_updated,
            indexed_at = CURRENT_TIMESTAMP
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute(sql, payload)
            conn.commit()


class ProjectBootstrapOrchestrator:
    """High-level OOP orchestration for first my_projects bootstrap."""

    def __init__(
        self,
        repo_path: Path,
        db_path: Path,
        schema_path: Path,
        branch: str = "main",
        docker_image: str = "alpine/git:latest",
    ) -> None:
        self.repo_path = repo_path.resolve()
        self.branch = branch
        self.reader = DockerGitRepositoryReader(
            repo_path=self.repo_path,
            branch=branch,
            docker_image=docker_image,
        )
        self.parser = ReadmeProjectParser()
        self.gateway = ProjectRepositoryGateway(db_path=db_path, schema_path=schema_path)

    def run(self) -> None:
        """Execute full bootstrap workflow with robust logging and error handling."""
        LOGGER.info("Starting bootstrap for repository: %s", self.repo_path)

        readme = self.reader.read_readme_from_branch()
        description, languages, technologies = self.parser.parse(readme)

        project = ProjectRecord(
            repo_name=self.repo_path.name,
            repo_url=self._resolve_remote_url(),
            description=description,
            languages=languages,
            technologies=technologies,
            readme_full_text=readme,
            stars=None,
            last_updated=date.today().isoformat(),
        )

        self.gateway.ensure_schema()
        self.gateway.upsert_project(project)

        LOGGER.info(
            "Bootstrap complete: repo=%s languages=%s technologies=%s",
            project.repo_name,
            ",".join(project.languages) if project.languages else "none",
            ",".join(project.technologies) if project.technologies else "none",
        )

    def _resolve_remote_url(self) -> str:
        command = ["git", "-C", str(self.repo_path), "remote", "get-url", "origin"]
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            value = result.stdout.strip()
            if value:
                return value
        return f"file://{self.repo_path}"


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap my_projects from repository README using containerized git read."
    )
    parser.add_argument("--repo-path", default=".", help="Local git repository path")
    parser.add_argument("--branch", default="main", help="Target branch to read README from")
    parser.add_argument(
        "--db-path",
        default="db/recruitment_assistant.db",
        help="SQLite database path",
    )
    parser.add_argument(
        "--schema-path",
        default="db/schema_init.sql",
        help="Schema file used to initialize DB when needed",
    )
    parser.add_argument(
        "--docker-image",
        default="alpine/git:latest",
        help="Docker image used to access repository in isolation",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for orchestration module."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    orchestrator = ProjectBootstrapOrchestrator(
        repo_path=Path(args.repo_path),
        db_path=Path(args.db_path),
        schema_path=Path(args.schema_path),
        branch=args.branch,
        docker_image=args.docker_image,
    )

    try:
        orchestrator.run()
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Bootstrap failed")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
