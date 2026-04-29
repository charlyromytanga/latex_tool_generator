# Dockerfile — service API (FastAPI)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_SYSTEM_PYTHON=1

# Installer les dépendances via pyproject.toml (groupe api)
COPY pyproject.toml uv.lock ./
RUN uv pip install --system ".[api]"

# Télécharger les modèles spaCy
RUN python -m spacy download fr_core_news_md \
    && python -m spacy download en_core_web_md \
    && python -m spacy download en_core_web_sm

# Copier le code source
COPY src/ ./src/
COPY db/ ./db/

RUN mkdir -p /app/runs/tmp/api_uploads /app/db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENV PYTHONPATH=/app/src
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
