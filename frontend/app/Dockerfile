# Dockerfile — service App (Streamlit), multi-stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /install

# Installer uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_SYSTEM_PYTHON=1

# Dépendances système pour la compilation des wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances via pyproject.toml (groupe app)
COPY pyproject.toml uv.lock ./
RUN uv pip install --system --prefix=/install/deps ".[app]"

# --- Image finale, légère ---
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python installées depuis l'étape builder
COPY --from=builder /install/deps /usr/local

# Copier le code de l'application
COPY src/ src/
COPY templates/ templates/
COPY data/schemas/ data/schemas/

# Config Streamlit
RUN mkdir -p ~/.streamlit && \
    printf '[client]\nshowErrorDetails = false\n' > ~/.streamlit/config.toml

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/app/entry.py", "--server.port=8501", "--server.address=0.0.0.0"]
