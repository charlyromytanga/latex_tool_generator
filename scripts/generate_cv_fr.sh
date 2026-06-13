#!/usr/bin/env bash
# Usage: bash scripts/generate_cv_fr.sh <cv_base_id> <job_id> [db_path]
#
# Generates:
#   shared/output/archiv_{job_id}_{cv_base_id}_{mm}_{yyyy}.tex
#   shared/output/{LASTNAME}_{Firstname}_{Company}_{mm}_{yyyy}.pdf
set -e

CV_BASE_ID="${1:?Usage: $0 <cv_base_id> <job_id> [db_path]}"
JOB_ID="${2:?Usage: $0 <cv_base_id> <job_id> [db_path]}"
DB_PATH="${3:-backend/db/jobcv.db}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 - <<PYEOF
import sys
sys.path.insert(0, "$REPO_ROOT")
from backend.services.cv.core.cv_utils import CVLatexGeneratorFR

gen = CVLatexGeneratorFR.from_db(
    db_path="$DB_PATH",
    cv_base_id="$CV_BASE_ID",
    job_id="$JOB_ID",
    max_experiences=3,
    max_projects=2,
    max_competences_techniques=5,
)
tex_path, pdf_path = gen.generate()
print(f"TEX: {tex_path}")
print(f"PDF: {pdf_path}")
PYEOF
