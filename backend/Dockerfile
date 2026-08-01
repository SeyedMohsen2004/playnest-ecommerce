FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6

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
