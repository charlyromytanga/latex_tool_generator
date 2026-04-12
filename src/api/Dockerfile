
# Dockerfile pour le service FastAPI API (chemin contextuel : src/api/)
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

# Installer uv (gestionnaire de dépendances rapide)
RUN pip install --upgrade pip uv

# Étape 1 : Copier et installer les dépendances Python (requirements.txt local à src/api/)
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Étape 2 : Installer les modèles spaCy nécessaires
RUN python -m spacy download fr_core_news_md && python -m spacy download en_core_web_md && python -m spacy download en_core_web_sm 

# Copier les fichiers de métadonnées du projet (depuis la racine du projet)
COPY ../../pyproject.toml ../../README.md ./

# Copier le code source principal (src/ du projet complet)
COPY ../../src ./src

# Créer les dossiers runtime nécessaires
RUN mkdir -p /app/runs/tmp/api_uploads /app/db

EXPOSE 8000

# Healthcheck aligné avec la route API actuelle
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENV PYTHONPATH=/app/src
# Entrypoint FastAPI (chemin correct depuis /app)
CMD ["uvicorn", "src.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
