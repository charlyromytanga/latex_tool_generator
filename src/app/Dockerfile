

# Dockerfile optimisé pour le service App (Streamlit)
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /install

# Dépendances système minimales pour builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install/deps --no-cache-dir -r requirements.txt

# Étape 2 : image finale, légère
FROM python:3.12-slim

WORKDIR /app

# Dépendances système minimales (runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
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
    echo "[client]\nshowErrorDetails = false\n" > ~/.streamlit/config.toml

EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande de lancement unique
CMD ["streamlit", "run", "src/app/entry.py", "--server.port=8501", "--server.address=0.0.0.0"]
