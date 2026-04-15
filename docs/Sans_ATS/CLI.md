# CLI

Primary entrypoint:

```bash
uv run cvrepo <command>
```

## Commands

- `generate <offer>`: shortest path from a raw offer to a CV and a cover letter.
- `analyze <input>`: analyze a raw job posting into JSON and LaTeX summary files.
- `render <summary>`: render a PDF from a summary JSON and a template.
- `archive`: copy rendered PDFs from `runs/render/` into `runs/archive/`.
- `validate`: inspect the job offer tree and report metadata gaps.
- `index-archive`: rebuild `runs/archive/index.jsonl`.

## Makefile facade

- `make uv-sync`
- `make generate OFFER=... DOC_LANG=fr`
- `make build_principal`
- `make archive`
- `make validate`
- `make index-archive`
