
# Dockerfile pour le service App (Streamlit)
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

# Installer les dépendances Python spécifiques à l'app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip install --upgrade pip


# Copier le code source (build context = racine du projet)
COPY src ./src

EXPOSE 8501
ENV PYTHONPATH=/app/src
CMD ["streamlit", "run", "src/app/main.py"]
