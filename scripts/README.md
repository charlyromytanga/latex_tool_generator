# Scripts

This directory now contains only helper scripts that complement the unified CLI.

## Current Status

- `job_offer.txt`: sample raw offer text for end-to-end generation experiments.
- non-Python helper assets stay here; Python orchestration lives under `src/`.

## Preferred Interface

```bash
uv sync
uv run cvrepo generate data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md --language fr --archive
```
