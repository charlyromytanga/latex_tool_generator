"""Project bootstrap orchestration.

This module reads repository metadata from the README on a target git branch
using a Docker container, then persists parsed data into the `my_projects`
SQLite table.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from orchestration.config import OrchestrationConfig
from orchestration.database import Database, detect_database_backend, normalize_database_url


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

    def __init__(self, database: Database, schema_path: Path) -> None:
        self.database = database
        self.schema_path = schema_path.resolve()

    def ensure_schema(self) -> None:
        """Create schema from file if my_projects table is missing."""
        if self.database.has_table("my_projects"):
            return

        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        LOGGER.info("my_projects missing, initializing schema from %s", self.schema_path)
        self.database.execute_script(self.schema_path.read_text(encoding="utf-8"))

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

        self.database.execute(sql, payload)


class ProjectBootstrapOrchestrator:
    """High-level OOP orchestration for first my_projects bootstrap."""

    def __init__(
        self,
        repo_path: Path,
        database_url: str,
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
        self.gateway = ProjectRepositoryGateway(
            database=Database(database_url),
            schema_path=schema_path,
        )

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
        "--database-url",
        default=None,
        help="Database URL override (postgresql://... or sqlite:///...)",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="SQLite database path fallback (used when --database-url is not set)",
    )
    parser.add_argument(
        "--schema-path",
        default=None,
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
    parser.add_argument(
        "--all-json",
        action="store_true",
        help="Insère tous les projets JSON trouvés dans data/projects/ au lieu du README du repo courant."
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for orchestration module."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    root = Path(__file__).resolve().parents[2]
    config = OrchestrationConfig.from_repo_root(root)
    db_path = Path(args.db_path) if args.db_path else config.db_path
    database_url = normalize_database_url(
        args.database_url or os.getenv("DATABASE_URL") or f"sqlite:///{db_path}",
        root,
        db_path,
    )
    backend = detect_database_backend(database_url)
    schema_path = (
        Path(args.schema_path)
        if args.schema_path
        else (config.postgres_schema_path if backend == "postgresql" else config.sqlite_schema_path)
    )

    if getattr(args, "all_json", False):
        # Mode insertion de tous les projets JSON
        from uuid import uuid4
        projects_dir = Path("data/projects")
        if not projects_dir.exists():
            LOGGER.error("Le dossier data/projects/ n'existe pas.")
            return 1
        import json as pyjson
        from orchestration.database import Database
        db = Database(database_url)
        # S'assurer que la table existe
        gateway = ProjectRepositoryGateway(db, schema_path)
        gateway.ensure_schema()
        count = 0
        for json_path in projects_dir.glob("*.json"):
            with open(json_path, "r", encoding="utf-8") as f:
                data = pyjson.load(f)
            payload = {
                "project_id": str(uuid4()),
                "repo_name": data.get("repo_name", ""),
                "repo_url": data.get("repo_url", f"file://{json_path.stem}"),
                "description": data.get("description", ""),
                "languages_json": pyjson.dumps(data.get("languages", {}), ensure_ascii=True),
                "technologies_json": pyjson.dumps(data.get("stack", {}), ensure_ascii=True),
                "readme_full_text": data.get("description", ""),
                "stars": None,
                "last_updated": None,
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
            db.execute(sql, payload)
            count += 1
            LOGGER.info(f"Projet inséré/MAJ : {payload['repo_name']}")
        LOGGER.info(f"Insertion terminée : {count} projets traités.")
        return 0
    else:
        orchestrator = ProjectBootstrapOrchestrator(
            repo_path=Path(args.repo_path),
            database_url=database_url,
            db_path=db_path,
            schema_path=schema_path,
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
