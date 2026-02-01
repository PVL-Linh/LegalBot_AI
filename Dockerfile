# Dockerfile for LegalBot AI backend (FastAPI)
# Build with: docker build -t legalbot-backend .

FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000

WORKDIR /app

# Install build deps (adjust if your requirements need extra OS packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE ${PORT}

# Default start command (Render will set PORT env var)
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
