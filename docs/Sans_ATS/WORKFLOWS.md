# Workflows

## Generate a CV and a cover letter from one offer

```bash
uv run cvrepo generate data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md --language fr --archive
```

## Inspect the extracted summary only

```bash
uv run cvrepo analyze data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md
```

## Render a PDF from a summary

```bash
uv run cvrepo render runs/tmp/summaries/offer_20260219_quant_dev_junior_summary.json --template fr --output-dir runs/render --prefix cv_fr
```

## Validate the offers tree

```bash
uv run cvrepo validate --offers-root data/offers
```

## Archive rendered PDFs

```bash
uv run cvrepo archive --source-dir runs/render --archive-root runs/archive
uv run cvrepo index-archive --archive-root runs/archive
```

## Rebuild archive index

```bash
uv run cvrepo index-archive --archive-root runs/archive
```
