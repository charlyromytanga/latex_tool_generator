"""Root entrypoint for first orchestration bootstrap.

Usage:
    python main.py --branch main
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    """Make src/ importable when running from repository root."""
    root = Path(__file__).resolve().parent
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def main() -> int:
    """Run orchestrator from repository root with robust top-level error handling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("root-main")

    try:
        _bootstrap_import_path()
        from orchestration.orchestrator import main as orchestrator_main

        logger.info("Launching orchestration bootstrap from root main.py")
        return orchestrator_main()
    except Exception:  # pylint: disable=broad-except
        logger.exception("Fatal error in root main entrypoint")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
