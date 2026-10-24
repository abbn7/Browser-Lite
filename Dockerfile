# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ANONYMIZED_TELEMETRY=false BROWSER_USE_LOGGING_LEVEL=error PLAYWRIGHT_BROWSERS_PATH=/opt/browsers DATA_DIR=/data CHROMIUM_SANDBOX=false
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    playwright install --with-deps --no-shell chromium && apt-get update && apt-get install -y --no-install-recommends libnss3-tools && rm -rf /var/lib/apt/lists/*
COPY install_codex.py /tmp/install_codex.py
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    python /tmp/install_codex.py && rm /tmp/install_codex.py
RUN groupadd -g 10001 app && useradd -m -u 10001 -g app app && mkdir -p /data && chown app:app /data
COPY --chown=app:app . .
RUN chmod +x /app/start.sh
EXPOSE 8000
CMD ["/app/start.sh"]
