#!/bin/sh
set -eu
umask 077
# Railway volumes can arrive owned by root. Drop privileges before serving requests.
if [ "$(id -u)" = "0" ]; then
    mkdir -p "${DATA_DIR:-/data}"
    chown 10001:10001 "${DATA_DIR:-/data}"
    exec setpriv --reuid=10001 --regid=10001 --init-groups env HOME=/home/app /app/start.sh
fi
mkdir -p "${DATA_DIR:-/data}"
# Optional enterprise/test proxy CA; never disable TLS verification.
if [ -n "${BROWSER_CA_CERT:-}" ]; then
    mkdir -p "$HOME/.pki/nssdb"
    if [ ! -f "$HOME/.pki/nssdb/cert9.db" ]; then
        certutil -N -d "sql:$HOME/.pki/nssdb" --empty-password
    fi
    certutil -A -d "sql:$HOME/.pki/nssdb" -n browser-lite-proxy -t "C,," -i "$BROWSER_CA_CERT" -f /dev/null
fi
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --no-access-log --proxy-headers
