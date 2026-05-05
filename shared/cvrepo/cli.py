from __future__ import annotations

import argparse
import json
from pathlib import Path

from .archive_manager import archive_rendered_pdfs
from .job_parser import write_outputs
from .metadata import scan_archive, write_index
from .paths import ARCHIVE_DIR, OFFERS_DIR, RENDER_DIR, SUMMARIES_DIR, ensure_runtime_directories
from .pipeline import generate_application
from .template_engine import default_template, render_summary
from .validation import validate_offer_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cvrepo", description="Unified CLI for CV/LM repository automation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a CV and a cover letter directly from a raw offer")
    generate.add_argument("offer", help="Path to the raw job offer file")
    generate.add_argument("--language", choices=["fr", "en"], default="fr")
    generate.add_argument("--kind", choices=["both", "cv", "letter"], default="both")
    generate.add_argument("--output-dir", default=str(RENDER_DIR))
    generate.add_argument("--summaries-dir", default=str(SUMMARIES_DIR))
    generate.add_argument("--archive", action="store_true")
    generate.add_argument("--archive-root", default=str(ARCHIVE_DIR))

    analyze = subparsers.add_parser("analyze", help="Analyze a job posting into JSON/LaTeX summaries")
    analyze.add_argument("input", help="Path to the raw job posting file")
    analyze.add_argument("--outdir", default=str(SUMMARIES_DIR))
    analyze.add_argument("--format", choices=["json", "latex", "both"], default="both")

    render = subparsers.add_parser("render", help="Render a PDF from a summary JSON and a template")
    render.add_argument("summary", help="Path to a summary JSON file")
    render.add_argument("--template", default="fr", help="Template alias (fr, en, principal) or template directory")
    render.add_argument("--entrypoint", help="Template entrypoint filename")
    render.add_argument("--output-dir", default=str(RENDER_DIR))
    render.add_argument("--prefix")

    archive = subparsers.add_parser("archive", help="Archive rendered PDFs into runs/archive")
    archive.add_argument("--source-dir", default=str(RENDER_DIR))
    archive.add_argument("--archive-root", default=str(ARCHIVE_DIR))
    archive.add_argument("--delete-source", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate job offer metadata tree")
    validate.add_argument("--offers-root", default=str(OFFERS_DIR))

    index_archive = subparsers.add_parser("index-archive", help="Rebuild archive index.jsonl")
    index_archive.add_argument("--archive-root", default=str(ARCHIVE_DIR))

    return parser


def command_generate(args: argparse.Namespace) -> int:
    result = generate_application(
        offer_path=Path(args.offer),
        language=args.language,
        kind=args.kind,
        output_dir=Path(args.output_dir),
        summaries_dir=Path(args.summaries_dir),
        archive=args.archive,
        archive_root=Path(args.archive_root),
    )
    print(f"[summary] {result.summary}")
    if result.cv:
        print(f"[cv] {result.cv}")
    if result.letter:
        print(f"[letter] {result.letter}")
    for item in result.archived:
        print(f"[archived] {item.source} -> {item.destination}")
    if result.index:
        print(f"[index] {result.index}")
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    formats = ("json", "latex") if args.format == "both" else (args.format,)
    written = write_outputs(input_path, Path(args.outdir), formats=formats)
    for kind, path in written.items():
        print(f"[{kind}] {path}")
    return 0


def command_render(args: argparse.Namespace) -> int:
    summary_path = Path(args.summary)
    template_arg = Path(args.template) if Path(args.template).exists() else None
    template_dir = template_arg if template_arg else default_template(args.template)
    destination = render_summary(
        summary_path=summary_path,
        template_dir=template_dir,
        output_dir=Path(args.output_dir),
        entrypoint=args.entrypoint,
        prefix=args.prefix,
    )
    print(destination)
    return 0


def command_archive(args: argparse.Namespace) -> int:
    archived = archive_rendered_pdfs(Path(args.source_dir), Path(args.archive_root), delete_source=args.delete_source)
    for item in archived:
        print(f"{item.source} -> {item.destination}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    issues = validate_offer_tree(Path(args.offers_root))
    for issue in issues:
        location = f" ({issue.path})" if issue.path else ""
        print(f"[{issue.level}] {issue.message}{location}")
    return 0


def command_index_archive(args: argparse.Namespace) -> int:
    records = scan_archive(Path(args.archive_root))
    destination = write_index(records, destination=Path(args.archive_root) / "index.jsonl")
    print(destination)
    print(json.dumps({"records": len(records)}, ensure_ascii=False))
    return 0


def main() -> int:
    ensure_runtime_directories()
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "generate":
        return command_generate(args)
    if args.command == "analyze":
        return command_analyze(args)
    if args.command == "render":
        return command_render(args)
    if args.command == "archive":
        return command_archive(args)
    if args.command == "validate":
        return command_validate(args)
    if args.command == "index-archive":
        return command_index_archive(args)
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
