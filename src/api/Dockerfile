
# Dockerfile pour le service API (FastAPI)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python spécifiques à l'API
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip install --upgrade pip

# Installer les modèles spaCy français et anglais
RUN python -m spacy download fr_core_news_md 
RUN python -m spacy download  en_core_web_md

# Copier le code source
COPY src ./src

# Dossiers runtime utilisés par l'API
RUN mkdir -p /app/runs/tmp/api_uploads /app/db

EXPOSE 8000

# Healthcheck aligné sur la route API
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENV PYTHONPATH=/app/src
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
