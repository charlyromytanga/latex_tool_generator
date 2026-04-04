# Architecture

The repository is now organized around explicit zones, with source code centered in `src/`:

- `src/`: Python application code and unified CLI.
- `templates/`: LaTeX templates, letters, and archive sources.
- `data/`: offers, metadata, archive, and schemas.
- `runs/`: runtime outputs, archives, indexes, and temporary files.
- `docs/`: workflows, migration notes, CLI usage, and architectural guidance.

## Runtime Model

1. A raw job offer is stored in `data/offers/...`.
2. `cvrepo generate` analyzes the offer and writes a normalized summary under `runs/tmp/summaries/`.
3. The same command renders the CV and the cover letter from the canonical templates.
4. Rendered PDFs land in `runs/render/`.
5. With `--archive`, the generated PDFs are copied to `runs/archive/` and `runs/archive/index.jsonl` is refreshed.
