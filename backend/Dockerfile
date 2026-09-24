FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2

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
