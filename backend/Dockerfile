FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4

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
