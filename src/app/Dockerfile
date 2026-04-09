
# Dockerfile pour le service App (Streamlit)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
     && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python spécifiques à l'app
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --upgrade pip \
    && pip install --no-cache-dir streamlit
    
# Copy application code
COPY src/ src/
COPY templates/ templates/
COPY data/schemas/ data/schemas/

# Create streamlit config directory
RUN mkdir -p ~/.streamlit

# Create Streamlit configuration
RUN echo "[client]\nshowErrorDetails = false\n" > ~/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit (nouveau chemin après déplacement)
CMD ["streamlit", "run", "src/app/entry.py", "--server.port=8501", "--server.address=0.0.0.0"]
