# Dockerfile for FastAPI API service
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal system packages for build/runtime tooling.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*



# Étape 1 : Copier et installer les dépendances (profite du cache Docker si requirements.txt ne change pas)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip install --upgrade pip

# Étape 2 : Installer les modèles spaCy (cette étape sera cachée si requirements.txt n'a pas changé)
RUN python -m spacy download fr_core_news_md && python -m spacy download en_core_web_md


# Copier les fichiers de métadonnées du projet
COPY pyproject.toml README.md ./

# Copier le code source (cette étape ne casse pas le cache des dépendances)
COPY src ./src

# Runtime folders used by routes and local artifacts.
RUN mkdir -p /app/runs/tmp/api_uploads /app/db

EXPOSE 8000

# Health check aligned with current API route.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENV PYTHONPATH=/app/src
# FastAPI entrypoint (chemin correct depuis /app)
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
