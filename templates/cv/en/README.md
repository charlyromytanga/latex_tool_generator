# Modular EN template — how to use

Files added:

- `main.tex` : main template including modular sections.
- `sections/` : modifiable files for each section (header, profile, experience, certifications, skills, education).
- `variants/` : historical EN CV variants kept as secondary sources.

Quick usage:

1. Open `main.tex` and edit the top commands: `\cvname`, `\cvaddress`, `\cvmail`, `\cvphone`, `\cvlinkedin`, `\cvgithub`, `\jobtype`, `\presentation`.
2. Edit content in `sections/` to adapt experiences, skills, etc.
3. Build and PDF output to `runs/render`:

Use the Makefile or the CLI to render the PDF:

```bash
make generate OFFER=data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md DOC_LANG=en
# or
uv run cvrepo render runs/tmp/summaries/offer_20260219_quant_dev_junior_summary.json --template en
```

The render creates a PDF file in `runs/render`.

Tip: keep copies per position and change only the header macros for quick variants.
