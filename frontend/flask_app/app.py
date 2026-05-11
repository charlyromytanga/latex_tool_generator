"""Flask frontend application."""

from __future__ import annotations

import os
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
    generate_cv_fr,
    check_existing_pdf,
    get_pdf_bytes,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


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
        record = get_cv_base(record_id).get("data", {})
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


@app.route("/cv-base/<record_id>/delete", methods=["POST"])
def cv_base_delete(record_id):
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
        try:
            add_job(payload)
            flash("Job added", "success")
            return redirect(url_for("jobs_list"))
        except BackendApiError as e:
            flash(str(e), "error")
    return render_template("job_add.html")


@app.route("/jobs/<record_id>/delete", methods=["POST"])
def job_delete(record_id):
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
    try:
        cv_records = list_cv_base().get("data", [])
        job_records = list_jobs().get("data", [])
    except BackendApiError as e:
        error = str(e)
    return render_template(
        "generate.html",
        cv_records=cv_records,
        job_records=job_records,
        error=error,
    )


@app.route("/generate/api", methods=["POST"])
def generate_api():
    """Endpoint JSON async pour la génération de CV."""
    from flask import jsonify
    body = request.get_json(silent=True) or {}
    cv_id = body.get("cv_id", "").strip()
    job_id = body.get("job_id", "").strip()
    target_title_index = int(body.get("target_title_index", 0))

    if not cv_id or not job_id:
        return jsonify({"ok": False, "message": "CV et Job sont requis"}), 400

    # Vérifier si un PDF existe déjà ce mois-ci
    try:
        check = check_existing_pdf(cv_id, job_id)
        existing = check.get("data", {})
        if existing.get("exists") and not body.get("force", False):
            lang = existing.get("lang", "FR")
            return jsonify({"ok": True, "cached": True, "filename": existing["filename"], "lang": lang}), 200
    except BackendApiError:
        pass  # Si la vérif échoue, on continue vers la génération

    try:
        result = generate_cv_fr(cv_id, job_id, target_title_index)
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
