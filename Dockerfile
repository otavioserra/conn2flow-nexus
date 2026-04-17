# =============================================================================
# Conn2Flow Nexus AI - Dockerfile
# Multi-stage build for production-ready Python app
# =============================================================================

# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

LABEL maintainer="Conn2Flow <dev@conn2flow.com>"
LABEL description="Conn2Flow Nexus AI - AI Gateway"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/

# Non-root user for security
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
