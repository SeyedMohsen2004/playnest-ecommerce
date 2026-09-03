FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

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
