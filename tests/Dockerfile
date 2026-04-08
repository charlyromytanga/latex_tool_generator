# Dockerfile for running unit tests
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-test.txt .
COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -e .

# Set PYTHONPATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Create directory for artifacts
RUN mkdir -p /app/test-results /app/coverage-report

# Default command: run tests with coverage
CMD ["pytest", "tests/src_test", \
     "--cov=src", \
     "--cov-report=html:/app/coverage-report", \
     "--cov-report=term-missing", \
     "--cov-report=xml:/app/test-results/coverage.xml", \
     "-v", \
     "--tb=short"]
