FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-build.txt requirements.txt ./
RUN python -m pip install --require-hashes -r requirements-build.txt \
    && python -m pip install \
        --require-hashes \
        --no-build-isolation \
        -r requirements.txt \
    && python -m pip check

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
