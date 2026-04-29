# Dockerfile — service Runner (orchestration)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    postgresql-client \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    latexmk \
    && rm -rf /var/lib/apt/lists/*

# Installer uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_SYSTEM_PYTHON=1

# Installer les dépendances via pyproject.toml (groupe runner)
COPY pyproject.toml uv.lock ./
RUN uv pip install --system ".[runner]"

# Copier le code source
COPY src ./src
COPY db ./db
COPY templates ./templates
COPY data ./data
COPY scripts ./scripts

RUN chmod +x scripts/*.sh

RUN mkdir -p runs/run_cv runs/run_letter runs/run_thank_you \
    runs/run_recruiter_email runs/run_project_report runs/run_thesis

CMD ["python", "-m", "src.db_orchestration.orchestrator"]
