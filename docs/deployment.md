# Production Deployment

This document describes an opt-in manual deployment workflow. It has not been
used to deploy the current server. Confirm the real server topology, backup
locations, reverse proxy, DNS, and storage arrangements before using it.

## Architecture

`docker-compose.prod.yml` runs three services:

- PostgreSQL 16 on an internal Docker network with a persistent named volume.
- Django under Gunicorn as a non-root user, with named static and media volumes.
- A non-root Next.js standalone production server.

The API and frontend publish to loopback by default so a host-level reverse
proxy can reach them without exposing the container ports publicly. No internal
TLS terminator or Nginx service is included. A containerized reverse proxy would
need to join the production network or use another explicitly reviewed topology.

The development `docker-compose.yml`, development Dockerfiles, Django
`runserver`, and Next.js development server remain separate and unchanged.

## Prerequisites

- Docker Engine and Docker Compose v2.
- A production host with adequate disk, memory, and backup capacity.
- DNS and an external reverse proxy capable of terminating HTTPS.
- Confirmed PostgreSQL and media backup and restore procedures.
- Production SMS and payment credentials supplied out of band.
- An operator-approved maintenance and rollback window.

Copy the tracked template and protect the resulting file:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Replace every placeholder. Never commit `.env.production`.

## Required Environment

Private values:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Long, unique Django signing secret. |
| `POSTGRES_DB` | Production database name. |
| `POSTGRES_USER` | Production database role. |
| `POSTGRES_PASSWORD` | Production database password. |
| `KAVENEGAR_API_KEY` | Production SMS provider API key. |
| `ZARINPAL_MERCHANT_ID` | Production payment merchant identifier. |

Public routing values:

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-visible API base URL, including `/api/v1`. |
| `FRONTEND_BASE_URL` | Public storefront origin used for backend redirects. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated public API hostnames. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins, including schemes. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated storefront origins allowed by CORS. |
| `ZARINPAL_CALLBACK_URL` | Public HTTPS payment callback URL. |

Security and integration policy:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECURE_SSL_REDIRECT` | Explicitly enables or disables Django HTTPS redirects. |
| `DJANGO_SECURE_HSTS_SECONDS` | HSTS duration; keep `0` until HTTPS is verified. |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | Enables HSTS for all subdomains. |
| `DJANGO_SECURE_HSTS_PRELOAD` | Enables the HSTS preload directive. |
| `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF` | Controls the `nosniff` security header. |
| `DJANGO_SECURE_REFERRER_POLICY` | Sets the response referrer policy. |
| `DJANGO_SESSION_COOKIE_SECURE` | Requires HTTPS for session cookies. |
| `DJANGO_CSRF_COOKIE_SECURE` | Requires HTTPS for CSRF cookies. |
| `DJANGO_TRUST_X_FORWARDED_PROTO` | Trusts the proxy-provided HTTPS scheme header. |
| `SMS_PROVIDER` | SMS backend; production normally uses `kavenegar`. |
| `KAVENEGAR_SENDER` | Optional sender when a verification template is not used. |
| `KAVENEGAR_VERIFY_TEMPLATE` | Optional Kavenegar verification template. |
| `ZARINPAL_SANDBOX` | Explicit payment gateway sandbox selection. |

Container and process configuration:

| Variable | Purpose |
| --- | --- |
| `PRODUCTION_COMPOSE_PROJECT_NAME` | Isolates production containers and volumes. |
| `API_IMAGE` | Versioned backend image tag. |
| `FRONTEND_IMAGE` | Versioned frontend image tag. |
| `PRODUCTION_BIND_ADDRESS` | Host bind address; defaults to loopback. |
| `PRODUCTION_API_PORT` | Host port mapped to Gunicorn. |
| `PRODUCTION_FRONTEND_PORT` | Host port mapped to Next.js. |
| `GUNICORN_BIND` | Internal Gunicorn bind address. |
| `GUNICORN_WORKERS` | Gunicorn worker count. |
| `GUNICORN_TIMEOUT` | Request timeout in seconds. |
| `GUNICORN_GRACEFUL_TIMEOUT` | Graceful shutdown timeout in seconds. |
| `GUNICORN_ACCESS_LOGFILE` | Access log target; `-` writes to stdout. |
| `GUNICORN_ERROR_LOGFILE` | Error log target; `-` writes to stderr. |

`NEXT_PUBLIC_API_BASE_URL` is embedded into browser bundles during the frontend
build. Changing it requires rebuilding the frontend image, not only restarting
the container.

## Pre-deployment Backup

The current server may not use this Compose project. Identify its actual
database and media locations first. Do not run these commands against an
unconfirmed target.

For an existing stack already managed by `docker-compose.prod.yml`, create a
database backup:

```bash
mkdir -p backups
docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec -T db sh -c 'pg_dump --username "$POSTGRES_USER" "$POSTGRES_DB"' \
  > backups/database-before-deploy.sql
```

Back up uploaded media independently:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec -T api tar -C /app/media -czf - . \
  > backups/media-before-deploy.tar.gz
```

Verify that both backups are non-empty and test restoration in a disposable
environment. Database backups and media backups must represent a compatible
point in time.

## Validate and Build

Validate interpolation without starting services:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  config --quiet
```

Use versioned `API_IMAGE` and `FRONTEND_IMAGE` tags so previous images remain
available for rollback, then build:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  build api frontend
```

Run Django's deployment checks inside the production image:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  run --rm --no-deps api python manage.py check --deploy
```

Review every warning. Do not silence HSTS, HTTPS, cookie, host, or schema
warnings merely to make the command quiet.

## Migrations and Static Files

Start PostgreSQL first:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  up -d db
```

Inspect the migration plan before applying it:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  run --rm api python manage.py migrate --plan
```

After operator review and a verified backup, apply migrations explicitly:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  run --rm api python manage.py migrate --noinput
```

The production image never migrates or loads seed data automatically.

Collect static files into the persistent static volume:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  run --rm api python manage.py collectstatic --noinput
```

Uploaded media uses a separate named volume and is never baked into an image.
The external reverse proxy must either have read-only access to the static and
media volumes or use an operator-approved host/external-storage arrangement.
Django does not serve media when `DEBUG=False`.

Treat uploaded media as untrusted content. Do not allow execution, prefer a
separate media origin where practical, preserve `nosniff`, and configure safe
content types and download behavior.

## Start or Update

Start the application services after migrations and static collection:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  up -d api frontend
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

For a later image update, repeat backup, validation, build, migration review,
migration, and collectstatic before recreating the services.

Never use `docker compose down --volumes` in production unless permanent data
deletion is explicitly intended and independently backed up.

## Health Verification

Container health checks use only Python and Node.js already present in the
images. Verify internal status:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec api python -c \
  "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/v1/health/', headers={'X-Forwarded-Proto': 'https'}); print(urllib.request.urlopen(request).status)"
docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec frontend node -e \
  "fetch('http://127.0.0.1:3000/').then(r => console.log(r.status))"
```

Then verify the public HTTPS storefront, API health endpoint, static files, and
a known media object through the external reverse proxy.

## Reverse Proxy and HTTPS

The external reverse proxy is responsible for:

- TLS certificates and HTTPS termination.
- Routing storefront traffic to the frontend service.
- Routing API and admin traffic to the API service.
- Serving or safely proxying `/static/` and `/media/`.
- Request-size, timeout, rate-limit, and access-log policies.
- Replacing, rather than appending to, untrusted forwarded headers.

Set `DJANGO_TRUST_X_FORWARDED_PROTO=True` only when the proxy removes any
client-supplied `X-Forwarded-Proto` header and sets it from the actual connection
scheme. Keep API ports private or loopback-bound. Incorrect trust can let a
client spoof secure requests; missing trust while SSL redirect is enabled can
cause redirect loops.

Start with `DJANGO_SECURE_HSTS_SECONDS=0`. Increase it only after HTTPS,
redirects, and subdomain coverage are verified. HSTS preload and subdomain
coverage can have long-lived consequences and require separate approval.

## Rollback

For an application-only rollback:

1. Keep the previous versioned API and frontend images.
2. Restore their tags in `.env.production`.
3. Recreate only `api` and `frontend` with `--no-build`.
4. Verify container and public health endpoints.

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml \
  up -d --no-build api frontend
```

Do not automatically reverse Django migrations. Review whether migrations are
reversible and whether old application code is compatible with the migrated
schema. If not, stop writes and restore the verified database and matching media
backups according to the operator-approved recovery procedure.

This production-readiness change adds no migrations.
