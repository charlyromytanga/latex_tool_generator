# Dockerfile — tests unitaires et d'intégration
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_SYSTEM_PYTHON=1

# Installer les dépendances via pyproject.toml (groupe test)
COPY pyproject.toml uv.lock ./
COPY src/ src/
COPY tests/ tests/

RUN uv pip install --system -e ".[test]"

ENV PYTHONPATH=/app/src:$PYTHONPATH

RUN mkdir -p /app/test-results /app/coverage-report

CMD ["pytest", "tests/src_test", \
     "--cov=src", \
     "--cov-report=html:/app/coverage-report", \
     "--cov-report=term-missing", \
     "--cov-report=xml:/app/test-results/coverage.xml", \
     "-v", \
     "--tb=short"]
