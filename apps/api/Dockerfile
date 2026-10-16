# syntax=docker/dockerfile:1
# Build from the REPO ROOT:  docker build -f apps/api/Dockerfile -t leaseguard-api .

# ---------- stage 1: dependencies + bake the sample lease ----------
FROM python:3.11-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build

COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --prefix=/install -r requirements.txt

# Generate athens_student_lease_sample.pdf at build time so the zero-login demo works on ephemeral disks.
COPY packages/sample-data /build/sample-data
RUN PYTHONPATH=/install/lib/python3.11/site-packages python /build/sample-data/generate_sample_lease.py \
 && test -s /build/sample-data/athens_student_lease_sample.pdf \
 && test -s /build/sample-data/georgia_statutes.json

# ---------- stage 2: slim runtime ----------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    SAMPLE_DATA_DIR=/app/packages/sample-data \
    SQLITE_PATH=/tmp/leaseguard_local.sqlite3
WORKDIR /app

COPY --from=builder /install /usr/local
COPY apps/__init__.py ./apps/__init__.py
COPY apps/api ./apps/api
COPY --from=builder /build/sample-data ./packages/sample-data
RUN touch packages/__init__.py && useradd --create-home --uid 10001 leaseguard && chown -R leaseguard /app
USER leaseguard

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT','8000'), timeout=4)" || exit 1

# Render / Railway inject $PORT; default 8000 locally. Proxy headers so SSE works behind their edge.
CMD ["sh", "-c", "exec uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
