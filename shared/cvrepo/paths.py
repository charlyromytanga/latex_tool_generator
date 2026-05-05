from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OFFERS_DIR = DATA_DIR / "offers"
SCHEMAS_DIR = DATA_DIR / "schemas"
TEMPLATES_DIR = REPO_ROOT / "templates"
CV_TEMPLATES_DIR = TEMPLATES_DIR / "cv"
LETTER_TEMPLATES_DIR = TEMPLATES_DIR / "letters"
ARCHIVE_TEMPLATES_DIR = TEMPLATES_DIR / "archive"
PRINCIPAL_TEMPLATE_DIR = CV_TEMPLATES_DIR / "principal"
FR_TEMPLATE_DIR = CV_TEMPLATES_DIR / "fr"
EN_TEMPLATE_DIR = CV_TEMPLATES_DIR / "en"
FR_LETTER_TEMPLATE_DIR = LETTER_TEMPLATES_DIR / "fr"
EN_LETTER_TEMPLATE_DIR = LETTER_TEMPLATES_DIR / "en"
RUNS_DIR = REPO_ROOT / "runs"
RENDER_DIR = RUNS_DIR / "render"
ARCHIVE_DIR = RUNS_DIR / "archive"
TMP_DIR = RUNS_DIR / "tmp"
SUMMARIES_DIR = TMP_DIR / "summaries"
INDEX_PATH = ARCHIVE_DIR / "index.jsonl"


def ensure_runtime_directories() -> None:
    for directory in (
        DATA_DIR,
        TEMPLATES_DIR,
        CV_TEMPLATES_DIR,
        LETTER_TEMPLATES_DIR,
        ARCHIVE_TEMPLATES_DIR,
        PRINCIPAL_TEMPLATE_DIR,
        FR_TEMPLATE_DIR,
        EN_TEMPLATE_DIR,
        FR_LETTER_TEMPLATE_DIR,
        EN_LETTER_TEMPLATE_DIR,
        RUNS_DIR,
        RENDER_DIR,
        ARCHIVE_DIR,
        TMP_DIR,
        SUMMARIES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)
