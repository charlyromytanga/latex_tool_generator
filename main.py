"""Root entrypoint for first orchestration bootstrap.

Usage:
    python main.py --branch main
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence


def _bootstrap_import_path() -> None:
    """Make src/ importable when running from repository root."""
    root = Path(__file__).resolve().parent
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _parse_args(argv: Sequence[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Root dispatcher for orchestration modules")
    parser.add_argument(
        "--target",
        default="my_projects",
        choices=[
            "my_projects",
            "my_experiences",
            "formations_template",
            "offers_ingest",
            "offers_llm",
            "offers_pipeline",
        ],
        help="Select orchestration target",
    )
    return parser.parse_known_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run orchestrator from repository root with robust top-level error handling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("root-main")

    try:
        args, remaining = _parse_args(argv)
        _bootstrap_import_path()

        if args.target == "my_experiences":
            from db_orchestration.experiences_orchestrator import main as orchestrator_main
        elif args.target == "formations_template":
            from db_orchestration.formations_orchestrator import main as orchestrator_main
        elif args.target == "offers_ingest":
            from db_orchestration.ingest import main as orchestrator_main
        elif args.target == "offers_llm":
            from db_orchestration.llm_extractors import main as orchestrator_main
        elif args.target == "offers_pipeline":
            from db_orchestration.orchestrator import main as orchestrator_main
        else:
            from db_orchestration.projects_orchestrator import main as orchestrator_main

        logger.info("Launching orchestration target=%s from root main.py", args.target)
        return orchestrator_main(remaining)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Fatal error in root main entrypoint")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
