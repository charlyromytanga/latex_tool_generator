"""Flask frontend application."""

from __future__ import annotations

import os
import re
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import api_client as _api
from api_client import (
    BackendApiError,
    get_health,
    get_summary,
    list_cv_base,
    get_cv_base,
    ingest_cv_base,
    delete_cv_base,
    list_jobs,
    get_job,
    add_job,
    delete_job,
    generate_cv,
    get_pdf_bytes,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


def _normalize_lines(value: str | None) -> list[str]:
    if not value:
        return []
    lines: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        while line[:1] in {"-", "*", "•"}:
            line = line[1:].strip()
        if line:
            lines.append(line)
    return lines


def _preview(text: str, limit: int = 72) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _format_education_for_display(value: str | None) -> str:
    if not value:
        return ""

    normalized_lines: list[str] = []
    english_header_replacements = {
        "2022 - 2023 Preparatory Class for Grandes Écoles (CPGE).": "2022 - 2023 Preparatory Class for Grandes Écoles (CPGE) at Lycée Claude Bernard Paris.",
        "2020 - 2021 Preparatory Class for Grandes Écoles (CPGE).": "2020 - 2021 Preparatory Class for Grandes Écoles (CPGE) at Lycée Fénelon Paris.",
    }

    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if ". " in line:
            header, desc = line.split(". ", 1)
            header = re.sub(r"\s+\d{5}$", "", header.strip())
            header = english_header_replacements.get(f"{header}.", header + ".")[:-1]
            line = f"{header}. {desc.strip()}"
        else:
            line = re.sub(r"\s+\d{5}$", "", line)
            line = english_header_replacements.get(line, line)

        normalized_lines.append(line)

    return "\n".join(normalized_lines)


def _format_cv_base_record_for_display(record: dict) -> dict:
    if not record:
        return record

    formatted = dict(record)
    formatted["education"] = _format_education_for_display(record.get("education"))
    return formatted


def _build_generate_options(cv_record: dict) -> dict:
    experiences = _normalize_lines(cv_record.get("experience"))
    projects = _normalize_lines(cv_record.get("projects"))
    technical = _normalize_lines(cv_record.get("technical"))

    def _pack(lines: list[str]) -> list[dict]:
        return [
            {"index": idx, "label": f"{idx + 1:02d} · {_preview(line)}"}
            for idx, line in enumerate(lines)
        ]

    return {
        "experiences": _pack(experiences),
        "projects": _pack(projects),
        "competences_techniques": _pack(technical),
    }


def _parse_optional_index_list(value: object, field_name: str) -> list[int] | None:
    if value in (None, ""):
        return None
    if not isinstance(value, list):
        raise ValueError(f"'{field_name}' doit être une liste d'entiers.")
    parsed: list[int] = []
    for item in value:
        try:
            parsed_item = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"'{field_name}' doit contenir uniquement des entiers.") from exc
        if parsed_item < 0:
            raise ValueError(f"'{field_name}' doit contenir uniquement des entiers >= 0.")
        parsed.append(parsed_item)
    return parsed or None


@app.context_processor
def inject_config():
    return {"config": {"BACKEND_URL": _api.BACKEND_URL}}


# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    summary, health, error = {}, {}, None
    try:
        summary = get_summary().get("data", {})
        health = get_health()
    except BackendApiError as e:
        error = str(e)
    return render_template("index.html", summary=summary, health=health, error=error)


# ── CV Base ────────────────────────────────────────────────────────────────────
@app.route("/cv-base")
def cv_base_list():
    language = request.args.get("language", "")
    records, error = [], None
    try:
        records = list_cv_base(language or None).get("data", [])
    except BackendApiError as e:
        error = str(e)
    return render_template("cv_base.html", records=records, language=language, error=error)


@app.route("/cv-base/<record_id>")
def cv_base_detail(record_id):
    record, error = {}, None
    try:
        record = _format_cv_base_record_for_display(get_cv_base(record_id).get("data", {}))
    except BackendApiError as e:
        error = str(e)
    return render_template("cv_base_detail.html", record=record, error=error)


@app.route("/cv-base/ingest", methods=["POST"])
def cv_base_ingest():
    source = request.form.get("source", "").strip()
    if not source:
        flash("Filename is required (e.g. cv_base_fr.json)", "error")
        return redirect(url_for("cv_base_list"))
    try:
        result = ingest_cv_base(source)
        flash(result.get("message", "Ingested"), "success")
    except BackendApiError as e:
        flash(str(e), "error")
    return redirect(url_for("cv_base_list"))


def _check_delete_password() -> bool:
    """Vérifie le mot de passe de suppression depuis le formulaire POST."""
    pwd      = request.form.get('delete_password', '').strip()
    num_pwd  = os.environ.get('DELETE_NUMERIC_PASSWORD', '')
    word_pwd = os.environ.get('DELETE_WORD_PASSWORD', '')
    return bool(pwd) and pwd in (num_pwd, word_pwd)


@app.route("/cv-base/<record_id>/delete", methods=["POST"])
def cv_base_delete(record_id):
    if not _check_delete_password():
        flash('❌ Mot de passe de suppression incorrect.', 'error')
        return redirect(url_for("cv_base_list"))
    try:
        delete_cv_base(record_id)
        flash(f"Deleted {record_id}", "success")
    except BackendApiError as e:
        flash(str(e), "error")
    return redirect(url_for("cv_base_list"))


# ── Jobs ───────────────────────────────────────────────────────────────────────
@app.route("/jobs")
def jobs_list():
    records, error = [], None
    try:
        records = list_jobs().get("data", [])
    except BackendApiError as e:
        error = str(e)
    return render_template("jobs.html", records=records, error=error)


@app.route("/jobs/<record_id>")
def job_detail(record_id):
    record, error = {}, None
    try:
        record = get_job(record_id).get("data", {})
    except BackendApiError as e:
        error = str(e)
    return render_template("job_detail.html", record=record, error=error)


@app.route("/jobs/add", methods=["GET", "POST"])
def job_add():
    if request.method == "POST":
        payload = {k: v for k, v in request.form.items() if v.strip()}
        # Auto-générer l'ID si non fourni
        if not payload.get("id"):
            company = payload.get("company_name", "job").lower().replace(" ", "-")
            payload["id"] = f"offer-{company}-{uuid.uuid4().hex[:8]}"
        try:
            add_job(payload)
            flash(f"Job ajouté : {payload['id']}", "success")
            return redirect(url_for("jobs_list"))
        except BackendApiError as e:
            flash(str(e), "error")
    return render_template("job_add.html")


@app.route("/jobs/<record_id>/delete", methods=["POST"])
def job_delete(record_id):
    if not _check_delete_password():
        flash('❌ Mot de passe de suppression incorrect.', 'error')
        return redirect(url_for("jobs_list"))
    try:
        delete_job(record_id)
        flash(f"Deleted {record_id}", "success")
    except BackendApiError as e:
        flash(str(e), "error")
    return redirect(url_for("jobs_list"))


# ── Generate ───────────────────────────────────────────────────────────────────
@app.route("/generate", methods=["GET"])
def generate():
    cv_records, job_records, error = [], [], None
    cv_options = {}
    try:
        cv_records = list_cv_base().get("data", [])
        job_records = list_jobs().get("data", [])
        cv_options = {record["id"]: _build_generate_options(record) for record in cv_records if record.get("id")}
    except BackendApiError as e:
        error = str(e)
    return render_template(
        "generate.html",
        cv_records=cv_records,
        job_records=job_records,
        cv_options=cv_options,
        error=error,
    )


@app.route("/generate/api", methods=["POST"])
def generate_api():
    """Endpoint JSON async pour la génération de CV."""
    from flask import jsonify
    body = request.get_json(silent=True) or {}
    cv_id = body.get("cv_id", "").strip()
    job_id = body.get("job_id", "").strip()
    raw_target_title_index = body.get("target_title_index")

    if raw_target_title_index in (None, ""):
        target_title_index = 0
    else:
        target_title_index = int(raw_target_title_index)

    selected_experience_indices = _parse_optional_index_list(
        body.get("selected_experience_indices"),
        "selected_experience_indices",
    )
    selected_project_indices = _parse_optional_index_list(
        body.get("selected_project_indices"),
        "selected_project_indices",
    )
    selected_competence_technique_indices = _parse_optional_index_list(
        body.get("selected_competence_technique_indices"),
        "selected_competence_technique_indices",
    )

    if not cv_id or not job_id:
        return jsonify({"ok": False, "message": "CV et Job sont requis"}), 400

    if target_title_index < 0:
        return jsonify({"ok": False, "message": "Le target_title_index doit être >= 0."}), 400

    try:
        cv_base = get_cv_base(cv_id).get("data", {})
        language = (cv_base.get("language") or "fr").lower()
        result = generate_cv(
            cv_id,
            job_id,
            language=language,
            target_title_index=target_title_index,
            selected_experience_indices=selected_experience_indices,
            selected_project_indices=selected_project_indices,
            selected_competence_technique_indices=selected_competence_technique_indices,
            max_projects=0,
            max_experiences=0,
        )
        data = result.get("data", {})
        pdf_path = data.get("pdf", "")
        filename = pdf_path.split("/")[-1] if pdf_path else ""
        # Déduire la langue depuis le chemin (ex: .../output/FR/file.pdf)
        parts = pdf_path.replace("\\", "/").split("/")
        lang = "FR"
        if "output" in parts:
            idx = parts.index("output")
            if idx + 1 < len(parts) - 1:
                lang = parts[idx + 1].upper()
        return jsonify({"ok": True, "cached": False, "filename": filename, "lang": lang}), 200
    except ValueError as e:
        return jsonify({"ok": False, "message": str(e)}), 400
    except BackendApiError as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/generate/pdf/<lang>/<path:filename>")
@app.route("/generate/pdf/<path:filename>")
def download_pdf(filename: str, lang: str = "FR"):
    """Proxy : télécharge le PDF depuis le backend et le sert au navigateur."""
    try:
        content = get_pdf_bytes(filename, lang)
        return Response(
            content,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except BackendApiError as e:
        flash(str(e), "error")
        return redirect(url_for("generate"))


# ── Settings / Health ──────────────────────────────────────────────────────────
@app.route("/settings")
def settings():
    health, error = {}, None
    try:
        health = get_health()
    except BackendApiError as e:
        error = str(e)
    return render_template("settings.html", health=health, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
