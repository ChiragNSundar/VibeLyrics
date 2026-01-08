# VibeLyrics Docker Image
# Multi-stage build for optimized image size

FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Download NLTK data
RUN python -c "import nltk; nltk.download('wordnet', download_dir='/opt/nltk_data'); nltk.download('punkt', download_dir='/opt/nltk_data'); nltk.download('averaged_perceptron_tagger', download_dir='/opt/nltk_data')"


# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    NLTK_DATA=/opt/nltk_data \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash vibelyrics

# Copy virtual environment and NLTK data from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/nltk_data /opt/nltk_data

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vibelyrics:vibelyrics . .

# Create data directories
RUN mkdir -p /app/data /app/app/static/uploads && \
    chown -R vibelyrics:vibelyrics /app/data /app/app/static/uploads

# Switch to non-root user
USER vibelyrics

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run with Gunicorn + eventlet for WebSocket support
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
