from __future__ import annotations

import datetime
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .paths import (
    EN_LETTER_TEMPLATE_DIR,
    EN_TEMPLATE_DIR,
    FR_LETTER_TEMPLATE_DIR,
    FR_TEMPLATE_DIR,
    PRINCIPAL_TEMPLATE_DIR,
    RENDER_DIR,
    TMP_DIR,
)


def latex_escape(value: str | None, leading_space: bool = True) -> str:
    if value is None:
        return ""
    escaped = str(value).replace("\r", "")
    mapping = [
        ("\\", "\\textbackslash{}"),
        ("%", "\\%"),
        ("&", "\\&"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    if leading_space and escaped and not escaped[0].isspace():
        escaped = " " + escaped
    for source, replacement in mapping:
        escaped = escaped.replace(source, replacement)
    return escaped


def tokenize_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[\.!?])\s+", text) if part.strip()]


def merge_section_with_template(template_dir: Path, section_name: str, summary: dict[str, Any]) -> str:
    source = template_dir / "sections" / f"{section_name}.tex"
    if not source.exists():
        return ""
    raw_text = source.read_text(encoding="utf-8")
    if "\\begin{" in raw_text or "\\end{" in raw_text:
        return ""
    sentences = tokenize_sentences(raw_text)
    keywords = {str(item).lower() for item in summary.get("keywords", []) + summary.get("skills", [])}
    selected = [sentence for sentence in sentences if any(keyword in sentence.lower() for keyword in keywords)]
    unique: list[str] = []
    for sentence in selected:
        if sentence not in unique:
            unique.append(sentence)
    return ("\n\n".join(unique) + "\n\n") if unique else ""


def render_type_recherche(summary: dict[str, Any]) -> str:
    parts = [
        latex_escape(summary.get("employment_type") or "", leading_space=False),
        latex_escape(summary.get("title") or summary.get("profile") or "Targeted application", leading_space=False),
        latex_escape(summary.get("location") or "", leading_space=False),
    ]
    return "\\noindent\\textbf{" + " - ".join(part for part in parts if part) + "}\n\n"


def render_presentation(summary: dict[str, Any]) -> str:
    profile = summary.get("profile")
    if not profile:
        skills = ", ".join(summary.get("skills", [])[:6])
        profile = f"Candidate profile aligned with the target role. Key skills: {skills}."
    return "\\section*{Presentation}\n\\noindent " + latex_escape(profile, leading_space=False) + "\n\n"


def render_competences(summary: dict[str, Any]) -> str:
    skills = summary.get("skills") or []
    lines = ["% Competences and technologies"]
    if skills:
        lines.append("\\begin{itemize}[leftmargin=*,itemsep=2pt]")
        for skill in skills:
            lines.append(f"  \\item {latex_escape(skill, leading_space=False)}")
        lines.append("\\end{itemize}")
    keywords = summary.get("keywords") or []
    if keywords:
        lines.append("\\vspace{2pt}")
        lines.append("\\textit{Keywords:} " + ", ".join(latex_escape(keyword, leading_space=False) for keyword in keywords[:10]) + "\\\\")
    return "\n".join(lines) + "\n"


def render_experiences(summary: dict[str, Any]) -> str:
    lines = ["% Experience section"]
    experiences = summary.get("experiences") or []
    if experiences:
        for experience in experiences:
            lines.append(
                f"\\textbf{{{latex_escape(experience.get('title', ''), leading_space=False)} - {latex_escape(experience.get('organization', ''), leading_space=False)}}} "
                f"\\hfill \\textit{{{latex_escape(experience.get('period', ''), leading_space=False)}}}\\\\"
            )
            bullets = experience.get("bullets") or []
            if bullets:
                lines.append("\\begin{itemize}")
                for bullet in bullets:
                    lines.append(f"  \\item {latex_escape(bullet, leading_space=False)}")
                lines.append("\\end{itemize}")
    else:
        responsibilities = summary.get("responsibilities") or []
        if responsibilities:
            lines.append("\\begin{itemize}")
            for responsibility in responsibilities[:8]:
                lines.append(f"  \\item {latex_escape(responsibility, leading_space=False)}")
            lines.append("\\end{itemize}")
    return "\n".join(lines) + "\n"


def render_certifications(summary: dict[str, Any]) -> str:
    certifications = summary.get("certifications") or []
    lines = ["% Certifications", "\\begin{itemize}"]
    if certifications:
        for certification in certifications:
            lines.append(f"  \\item {latex_escape(certification, leading_space=False)}")
    else:
        lines.append("  \\item (No certification listed)")
    lines.append("\\end{itemize}")
    return "\n".join(lines) + "\n"


def render_formation(summary: dict[str, Any]) -> str:
    education = summary.get("education") or []
    lines = ["% Education"]
    if education:
        lines.append("\\begin{itemize}[leftmargin=*,itemsep=2pt]")
        for entry in education:
            lines.append(
                f"  \\item \\textbf{{{latex_escape(entry.get('degree', ''), leading_space=False)}}} - "
                f"\\textit{{{latex_escape(entry.get('school', ''), leading_space=False)} - {latex_escape(entry.get('period', ''), leading_space=False)}}}"
            )
        lines.append("\\end{itemize}")
    else:
        lines.append("\\textbf{Education:} See academic profile.\\")
    return "\n".join(lines) + "\n"


def detect_entrypoint(template_dir: Path) -> str:
    candidates = ["main.tex", "fr_main.tex", "en_main.tex", "main_template.tex", "main_template_en.tex"]
    for candidate in candidates:
        if (template_dir / candidate).exists():
            return candidate
    raise FileNotFoundError(f"No template entrypoint found in {template_dir}")


def detect_letter_entrypoint(template_dir: Path) -> str:
    candidates = ["main.tex", "generic.tex"]
    for candidate in candidates:
        if (template_dir / candidate).exists():
            return candidate
    raise FileNotFoundError(f"No cover-letter template entrypoint found in {template_dir}")


def assemble(template_dir: Path, summary: dict[str, Any], build_dir: Path, entrypoint: str | None = None) -> tuple[Path, Path]:
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    chosen_entrypoint = entrypoint or detect_entrypoint(template_dir)
    source_entrypoint = template_dir / chosen_entrypoint
    if not source_entrypoint.exists():
        raise FileNotFoundError(f"Template entrypoint not found: {source_entrypoint}")
    copied_entrypoint = build_dir / chosen_entrypoint
    copied_entrypoint.write_text(source_entrypoint.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8")

    sections_dir = build_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    header_src = template_dir / "sections" / "header.tex"
    if header_src.exists():
        sections_dir.joinpath("header.tex").write_text(header_src.read_text(encoding="utf-8"), encoding="utf-8")

    renderers = {
        "type_recherche": render_type_recherche,
        "presentation": render_presentation,
        "competences": render_competences,
        "experiences": render_experiences,
        "certifications": render_certifications,
        "formation": render_formation,
    }
    for section_name, renderer in renderers.items():
        prefix = merge_section_with_template(template_dir, section_name, summary)
        sections_dir.joinpath(f"{section_name}.tex").write_text(prefix + renderer(summary), encoding="utf-8")
    return build_dir, copied_entrypoint


def compile_pdf(build_dir: Path, entrypoint: str) -> Path:
    command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint]
    for _ in range(2):
        completed = subprocess.run(command, cwd=str(build_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout.decode("utf-8", errors="ignore"))
    return build_dir / f"{Path(entrypoint).stem}.pdf"


def move_to_render(pdf_path: Path, output_dir: Path | None = None, prefix: str = "cv") -> Path:
    render_dir = output_dir or RENDER_DIR
    render_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = render_dir / f"{prefix}_{timestamp}.pdf"
    shutil.move(str(pdf_path), str(destination))
    return destination


def default_template(language: str) -> Path:
    mapping = {
        "fr": FR_TEMPLATE_DIR,
        "en": EN_TEMPLATE_DIR,
        "principal": PRINCIPAL_TEMPLATE_DIR,
    }
    if language not in mapping:
        raise ValueError(f"Unsupported language/template key: {language}")
    return mapping[language]


def default_letter_template(language: str) -> Path:
    mapping = {
        "fr": FR_LETTER_TEMPLATE_DIR,
        "en": EN_LETTER_TEMPLATE_DIR,
    }
    if language not in mapping:
        raise ValueError(f"Unsupported cover-letter language: {language}")
    return mapping[language]


def summary_company(summary: dict[str, Any], language: str) -> str:
    company = str(summary.get("company") or "").replace("_", " ").strip()
    if company:
        return company.title()
    return "votre entreprise" if language == "fr" else "your team"


def summary_skill_excerpt(summary: dict[str, Any], limit: int = 4) -> str:
    skills = [str(skill) for skill in summary.get("skills", [])[:limit] if str(skill).strip()]
    return ", ".join(skills)


def summary_responsibility_excerpt(summary: dict[str, Any], limit: int = 3) -> str:
    responsibilities = [str(item) for item in summary.get("responsibilities", [])[:limit] if str(item).strip()]
    return " ".join(responsibilities)


def build_letter_context(summary: dict[str, Any], language: str) -> dict[str, str]:
    title = str(summary.get("title") or ("poste vise" if language == "fr" else "target role"))
    company = summary_company(summary, language)
    location = str(summary.get("location") or summary.get("city") or "")
    skills = summary_skill_excerpt(summary)
    responsibilities = summary_responsibility_excerpt(summary)
    qualification = next((str(item) for item in summary.get("qualifications", []) if str(item).strip()), "")

    if language == "fr":
        subject = f"Candidature - {title}"
        greeting = "Madame, Monsieur,"
        intro = (
            f"Je vous adresse ma candidature pour le poste de {title}"
            f" chez {company}" + (f", base a {location}" if location else "") + "."
        )
        body = (
            "Mon profil combine une approche quantitative et une execution orientee resultat"
            + (f", avec un socle technique autour de {skills}" if skills else "")
            + ". "
            + (responsibilities if responsibilities else "Je peux contribuer rapidement sur les missions clefs du poste.")
        )
        closing = (f"{qualification}. " if qualification else "") + "Je serais heureux d'echanger avec vous pour detailler la valeur que je peux apporter a l'equipe."
        signature = "Cordialement,"
    else:
        subject = f"Application - {title}"
        greeting = "Dear Hiring Team,"
        intro = (
            f"I am applying for the {title} role"
            f" at {company}" + (f" in {location}" if location else "") + "."
        )
        body = (
            "My background combines quantitative problem solving with practical delivery"
            + (f", supported by hands-on experience with {skills}" if skills else "")
            + ". "
            + (responsibilities if responsibilities else "I can contribute quickly to the core responsibilities of the role.")
        )
        closing = (f"{qualification}. " if qualification else "") + "I would welcome the opportunity to discuss how I can contribute to your team."
        signature = "Sincerely,"

    return {
        "SUBJECT": subject,
        "GREETING": greeting,
        "INTRO": intro,
        "BODY": body,
        "CLOSING": closing,
        "SIGNATURE": signature,
    }


def render_letter_source(template_dir: Path, summary: dict[str, Any], language: str) -> tuple[str, str]:
    entrypoint = detect_letter_entrypoint(template_dir)
    content = (template_dir / entrypoint).read_text(encoding="utf-8").replace("\r\n", "\n")
    for token, value in build_letter_context(summary, language).items():
        content = content.replace(f"{{{{{token}}}}}", latex_escape(value, leading_space=False))
    return entrypoint, content


def render_summary(summary_path: Path, template_dir: Path, output_dir: Path | None = None, entrypoint: str | None = None, prefix: str | None = None) -> Path:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    build_dir = TMP_DIR / f"{summary_path.stem}_build"
    _, copied_entrypoint = assemble(template_dir, summary, build_dir, entrypoint=entrypoint)
    pdf_path = compile_pdf(build_dir, copied_entrypoint.name)
    return move_to_render(pdf_path, output_dir=output_dir, prefix=prefix or summary_path.stem)


def render_letter(summary_path: Path, template_dir: Path, language: str, output_dir: Path | None = None, prefix: str | None = None) -> Path:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    build_dir = TMP_DIR / f"{summary_path.stem}_{language}_letter_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    entrypoint, source = render_letter_source(template_dir, summary, language)
    build_path = build_dir / Path(entrypoint).name
    build_path.write_text(source, encoding="utf-8")
    pdf_path = compile_pdf(build_dir, build_path.name)
    return move_to_render(pdf_path, output_dir=output_dir, prefix=prefix or f"lm_{summary_path.stem}")
