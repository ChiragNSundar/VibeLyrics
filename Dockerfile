# VibeLyrics Docker Image
# Multi-stage build for FastAPI Backend + React Frontend

# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    Start_Command="uvicorn backend.main:app --host 0.0.0.0 --port 5000"

WORKDIR /app

# Install system dependencies
# libsndfile1 and ffmpeg needed for audio analysis (librosa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/data /app/uploads/audio

# Copy Backend Code
COPY backend /app/backend
COPY run.py /app/

# Copy Built Frontend from Stage 1 (Optional: if serving static files from FastAPI)
# For this setup, we'll keep them separate or assume the user mounts them,
# BUT for a single container deploy, copying to a static folder is best.
# Creating a static directory for FastAPI to serve if configured.
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run Application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
