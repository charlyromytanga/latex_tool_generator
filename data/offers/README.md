# Offers

This directory is now the canonical source of job postings and their metadata.

## Canonical Structure

- `data/offers/2026/Q1/tier-1/...`
- `data/offers/2026/Q1/tier-2/...`
- `data/offers/2026/Q1/tier-3/...`
- `data/offers/_templates/offer_template.md`
- `data/offers/_templates/offer_metadata_template.json`

## Naming Conventions

- `role_slug.md`
- `role_slug.metadata.json`
- `offer_YYYYMMDD_<role>.md` remains accepted during migration

## Example Target Layout

- `data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md`
- `data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.metadata.json`

## Recommended Workflow

- Keep one offer per file.
- Add the source URL and the company context.
- Add or infer metadata before rendering a CV or cover letter.
- Preserve the raw posting to support future retargeting.
- Use `uv run cvrepo validate --offers-root data/offers` regularly.
