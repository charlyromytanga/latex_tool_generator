# Migration

## Cutover Completed

The repository has been fully cut over to canonical paths and the temporary compatibility layer has been removed.

## Canonical paths

- `data/offers`
- `templates/cv/principal`
- `templates/cv/fr`
- `templates/cv/en`
- `templates/letters/fr`
- `templates/letters/en`
- `templates/archive`
- `runs/render`
- `runs/archive`
- `runs/tmp/summaries`

## Operational guidance

1. Use `uv run cvrepo generate ...` as the default offer-to-documents path, and keep `analyze` or `render` only for debugging.
2. Use `make generate OFFER=... DOC_LANG=...`, `make build_principal`, `make archive`, and `make validate` as shortcuts.
3. Add `.metadata.json` files progressively next to important offers.
4. Use `runs/archive/index.jsonl` as the source of truth for generated outputs.
