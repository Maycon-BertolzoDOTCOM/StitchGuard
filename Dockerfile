# ==============================================================================
# Stage 1: Builder — dependencias de build + Python packages
# ==============================================================================
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==============================================================================
# Stage 2: Runtime — imagem final enxuta e segura
# ==============================================================================
FROM python:3.13-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system stitchguard \
    && useradd --system --gid stitchguard --no-create-home stitchguard

WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=stitchguard:stitchguard . .

RUN mkdir -p /app/tmp/artifacts && chown stitchguard:stitchguard /app/tmp/artifacts

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER stitchguard
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

CMD ["uvicorn", "application.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
