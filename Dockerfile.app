# Dockerfile pour Streamlit (App Service)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .
COPY src/app/requirements.txt requirements-app.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-app.txt

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

# Run Streamlit
CMD ["streamlit", "run", "src/app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
