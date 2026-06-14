#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
python - <<'PY'
import os
import socket
import time

host = os.environ["POSTGRES_HOST"]
port = int(os.environ["POSTGRES_PORT"])

while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(1)
PY
echo "PostgreSQL is available."

python manage.py migrate --noinput

exec "$@"
