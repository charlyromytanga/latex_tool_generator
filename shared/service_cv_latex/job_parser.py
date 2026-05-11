from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .metadata import slugify


COMMON_SKILLS = [
    "Power BI", "PowerBI", "Alteryx", "SQL", "Python", "PySpark", "Pandas",
    "Tableau", "Google Data Studio", "Docker", "Git", "Java", "C++",
    "Spark", "NumPy", "scikit-learn", "Machine Learning", "ETL",
    "Data Engineer", "Data Analyst", "Azure", "AWS", "GCP",
]

RESPONSIBILITY_VERBS = [
    "identifier", "extraire", "collecter", "effectuer", "créer", "assurer",
    "travailler", "automatiser", "analyser", "contribuer", "concevoir", "optimiser",
    "build", "develop", "maintain", "design", "deliver", "support",
]


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    headings = [
        "Description de l'entreprise", "Description du poste", "Qualifications", "Profil",
        "Tes missions", "Missions", "Responsibilities", "Profile", "Description",
    ]
    current_title = "body"
    current_lines: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if any(heading.lower() in stripped.lower() for heading in headings):
            if current_lines:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = stripped or "body"
            current_lines = []
            continue
        current_lines.append(line)
    if current_lines:
        sections[current_title] = "\n".join(current_lines).strip()
    return sections


def extract_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped if len(stripped.split()) <= 10 else stripped[:80]
    return ""


def extract_location(text: str) -> str:
    for candidate in ("Paris", "London", "Geneva", "Zurich", "Luxembourg"):
        if re.search(candidate, text, re.IGNORECASE):
            return candidate
    remote = re.search(r"(Remote|Télétravail|Hybrid)", text, re.IGNORECASE)
    return remote.group(1) if remote else ""


def extract_employment_type(text: str) -> str:
    patterns = {
        "Full-time": r"Temps plein|Temps complet|Full[- ]time|Permanent",
        "Internship": r"Stage|Internship|Intern",
        "Contract": r"CDD|contract|Contractor",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return ""


def extract_experience_years(text: str) -> int | None:
    matches = [
        re.search(r"(\d+)\s+ans", text),
        re.search(r"(?:at least|minimum)\s+(\d+)\s+(?:years|ans)", text, re.IGNORECASE),
        re.search(r"(\d+)\s+years?\s+experience", text, re.IGNORECASE),
    ]
    for match in matches:
        if match:
            return int(match.group(1))
    return None


def extract_skills(text: str) -> list[str]:
    found = {skill for skill in COMMON_SKILLS if re.search(re.escape(skill), text, re.IGNORECASE)}
    return sorted(found)


def extract_responsibilities(text: str) -> list[str]:
    sentences = re.split(r"(?<=[\.!?\n])\s+", text)
    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip() and any(verb in sentence.lower() for verb in RESPONSIBILITY_VERBS)
    ]


def extract_qualifications(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    selected = [
        line for line in lines
        if re.search(r"BAC|Master|Licence|Formation|expérience|experience|skill|compétenc", line, re.IGNORECASE)
    ]
    return selected or lines[:3]


def keywords_from_text(text: str) -> list[str]:
    frequency: dict[str, int] = {}
    stopwords = {"the", "and", "for", "with", "les", "des", "pour", "avec", "une", "dans"}
    for word in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9\+#]+", text):
        lowered = word.lower()
        if len(lowered) <= 3 or lowered in stopwords:
            continue
        frequency[lowered] = frequency.get(lowered, 0) + 1
    return [item[0] for item in sorted(frequency.items(), key=lambda entry: (-entry[1], entry[0]))[:15]]


def analyze_text(text: str) -> dict[str, Any]:
    sections = split_sections(text)
    responsibilities_source = "\n".join(
        value for key, value in sections.items() if re.search(r"mission|responsab|description|role", key, re.IGNORECASE)
    ) or sections.get("body", text)
    qualifications_source = "\n".join(
        value for key, value in sections.items() if re.search(r"qualif|profil|formation|requirements", key, re.IGNORECASE)
    ) or sections.get("body", text)
    return {
        "title": extract_title(text),
        "location": extract_location(text),
        "employment_type": extract_employment_type(text),
        "experience_years": extract_experience_years(text),
        "skills": extract_skills(text),
        "keywords": keywords_from_text(text),
        "responsibilities": extract_responsibilities(responsibilities_source),
        "qualifications": extract_qualifications(qualifications_source),
        "raw_content": text,
    }


def summary_to_latex(summary: dict[str, Any]) -> str:
    lines = ["% Generated LaTeX fragment from job posting", "\\section*{Job Posting Summary}"]
    lines.append(f"\\textbf{{Title}}: {summary.get('title', '')}\\\\")
    if summary.get("location"):
        lines.append(f"\\textbf{{Location}}: {summary['location']}\\\\")
    if summary.get("employment_type"):
        lines.append(f"\\textbf{{Employment}}: {summary['employment_type']}\\\\")
    if summary.get("experience_years") is not None:
        lines.append(f"\\textbf{{Experience}}: {summary['experience_years']} years\\\\")
    if summary.get("skills"):
        lines.append("\\textbf{Skills}: " + ", ".join(summary["skills"]) + "\\\\")
    if summary.get("responsibilities"):
        lines.append("\\textbf{Key responsibilities}:\\\\begin{itemize}")
        for responsibility in summary["responsibilities"][:6]:
            lines.append(f"  \\item {responsibility}")
        lines.append("\\end{itemize}")
    return "\n".join(lines)


def write_outputs(input_path: Path, output_dir: Path, formats: tuple[str, ...] = ("json", "latex")) -> dict[str, Path]:
    summary = analyze_text(input_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    base_name = f"{input_path.stem}_summary"
    if "json" in formats:
        json_path = output_dir / f"{base_name}.json"
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        written["json"] = json_path
    if "latex" in formats:
        tex_path = output_dir / f"{base_name}.tex"
        tex_path.write_text(summary_to_latex(summary), encoding="utf-8")
        written["latex"] = tex_path
    return written


def infer_offer_metadata(offer_path: Path, offers_root: Path) -> dict[str, Any]:
    relative = offer_path.resolve().relative_to(offers_root.resolve())
    parts = list(relative.parts)
    metadata = {
        "offer_id": slugify("-".join(parts)).replace("_md", ""),
        "path": str(relative),
        "company": parts[-2] if len(parts) >= 2 else "unknown",
        "role_slug": offer_path.stem,
        "source_format": offer_path.suffix.lower(),
    }
    if len(parts) >= 6:
        metadata.update(
            {
                "year": parts[0],
                "quarter": parts[1],
                "tier": parts[2],
                "country": parts[3],
                "city": parts[4],
            }
        )
    return metadata
