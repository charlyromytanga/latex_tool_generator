"""Streamlit entrypoint delegating to the modular OOP app package."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    """Make src/ importable when running streamlit from repository root."""
    current_file = Path(__file__).resolve()
    src_path = current_file.parents[1]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def main() -> None:
    """Run modular Streamlit application."""
    _bootstrap_import_path()
    from app.streamlit import run_streamlit_app

    run_streamlit_app()


if __name__ == "__main__":
    main()
