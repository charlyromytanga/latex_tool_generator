"""Backend API client for the Flask frontend."""

from __future__ import annotations

import os
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000")


class BackendApiError(Exception):
    pass


def _http_error_message(e: httpx.HTTPStatusError) -> str:
    """Return a human-readable error message from an HTTP error response."""
    try:
        body = e.response.json()
        msg = body.get("message") or body.get("error") or e.response.text
    except Exception:
        msg = e.response.text or "Erreur inconnue"
    return f"Erreur {e.response.status_code} : {msg}"


def _get(path: str, params: dict | None = None) -> dict:
    try:
        r = httpx.get(f"{BACKEND_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise BackendApiError(_http_error_message(e)) from e
    except Exception as e:
        raise BackendApiError(str(e)) from e


def _post(path: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{BACKEND_URL}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise BackendApiError(_http_error_message(e)) from e
    except Exception as e:
        raise BackendApiError(str(e)) from e


def _delete(path: str) -> dict:
    try:
        r = httpx.delete(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise BackendApiError(_http_error_message(e)) from e
    except Exception as e:
        raise BackendApiError(str(e)) from e


# --- Health ---
def get_health() -> dict:
    return _get("/health")


# --- DB summary ---
def get_summary() -> dict:
    return _get("/cv/db/summary")


# --- CV Base ---
def list_cv_base(language: str | None = None) -> dict:
    params = {"language": language} if language else {}
    return _get("/cv/db/cv_base", params)


def get_cv_base(record_id: str) -> dict:
    return _get(f"/cv/db/cv_base/{record_id}")


def ingest_cv_base(source: str) -> dict:
    return _post("/cv/db/cv_base", {"source": source})


def delete_cv_base(record_id: str) -> dict:
    return _delete(f"/cv/db/cv_base/{record_id}")


# --- Jobs ---
def list_jobs() -> dict:
    return _get("/cv/db/jobs")


def get_job(record_id: str) -> dict:
    return _get(f"/cv/db/jobs/{record_id}")


def add_job(payload: dict) -> dict:
    return _post("/cv/db/jobs", payload)


def delete_job(record_id: str) -> dict:
    return _delete(f"/cv/db/jobs/{record_id}")


# --- Generate ---
def generate_cv(
    cv_id: str,
    job_id: str,
    language: str = "fr",
    target_title_index: int = 0,
    selected_experience_indices: list[int] | None = None,
    selected_project_indices: list[int] | None = None,
    selected_competence_technique_indices: list[int] | None = None,
    max_projects: int | None = None,
    max_experiences: int | None = None,
) -> dict:
    lang = (language or "fr").lower()
    if lang not in {"fr", "en"}:
        raise BackendApiError(f"Langue de génération invalide : {language}")
    payload = {
        "cv_base_id": cv_id,
        "job_id": job_id,
        "target_title_index": target_title_index,
    }
    if selected_experience_indices is not None:
        payload["selected_experience_indices"] = selected_experience_indices
    if selected_project_indices is not None:
        payload["selected_project_indices"] = selected_project_indices
    if selected_competence_technique_indices is not None:
        payload["selected_competence_technique_indices"] = selected_competence_technique_indices
    if max_projects is not None:
        payload["max_projects"] = max_projects
    if max_experiences is not None:
        payload["max_experiences"] = max_experiences
    return _post(f"/cv/generate/{lang}", payload)


def get_pdf_bytes(filename: str, lang: str = "FR") -> bytes:
    try:
        r = httpx.get(f"{BACKEND_URL}/cv/output/{lang}/{filename}", timeout=15)
        r.raise_for_status()
        return r.content
    except httpx.HTTPStatusError as e:
        raise BackendApiError(_http_error_message(e)) from e
    except Exception as e:
        raise BackendApiError(str(e)) from e
