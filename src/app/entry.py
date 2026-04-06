"""Streamlit entrypoint déléguant vers le package OOP modulaire de l'app."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    """Rend src/ importable lors de l'exécution de streamlit depuis la racine du repo."""
    current_file = Path(__file__).resolve()
    src_path = current_file.parents[1]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def main() -> None:
    """Lance l'application Streamlit modulaire."""
    _bootstrap_import_path()
    from app.main import StreamlitApplication
    from app.utils_functions import AppSettings

    settings = AppSettings()
    app = StreamlitApplication(settings)
    app.run()


if __name__ == "__main__":
    main()
