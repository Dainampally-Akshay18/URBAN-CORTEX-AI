# ============================================================
# Urban Cortex AI – Backend Dockerfile
# ============================================================
# Multi-stage build for production-grade container
# ============================================================

# ── Stage 1: Base ──────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Stage 2: Dependencies ─────────────────────────────────────
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Application ──────────────────────────────────────
FROM dependencies AS application

# Copy application code
COPY . .

# Expose the backend port
EXPOSE 8000

# Health-check (matches /api/v1/system/health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/system/health')" || exit 1

# Start the FastAPI server via Uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
