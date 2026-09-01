# Production Deployment

This runbook describes a manual transition to the repository's existing
production images. It does not deploy the application. Every command must be
reviewed against the actual host before an operator runs it.

## Confirmed Host Topology

The audited IpakToys host uses Compose project `ipaktoys` with services `db`,
`api`, and `frontend`. PostgreSQL data is stored in the existing external Docker
volume `ipaktoys_postgres_data`. Host Nginx terminates HTTPS and routes loopback
ports `127.0.0.1:8000` and `127.0.0.1:3000`; it reads static and uploaded media
directly from `/opt/ipaktoys/backend/staticfiles` and
`/opt/ipaktoys/backend/media`.

The production Compose contract preserves that topology:

- PostgreSQL uses an explicitly named **external** volume. Compose cannot
  silently create an empty replacement.
- Gunicorn and Next.js publish only to a configurable loopback address.
- Static and media use configurable host bind mounts with automatic host-path
  creation disabled.
- Host Nginx remains outside Compose and unchanged.
- No production container startup command migrates, seeds, imports, or runs
  `collectstatic`.

The development Compose workflow remains separate and still uses Django
`runserver`, the Next.js development server, and development source mounts.
For a genuinely new installation, an operator must deliberately create and
name an empty PostgreSQL volume before first start; production Compose never
creates one implicitly.

## Production Environment Contract

Copy the tracked template, fill it from an approved secret source, and protect
it before use:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

For the confirmed live topology, the non-secret storage and routing values must
resolve to:

```dotenv
PRODUCTION_COMPOSE_PROJECT_NAME=ipaktoys
PRODUCTION_POSTGRES_VOLUME_NAME=ipaktoys_postgres_data
PRODUCTION_STATIC_PATH=/opt/ipaktoys/backend/staticfiles
PRODUCTION_MEDIA_PATH=/opt/ipaktoys/backend/media
PRODUCTION_BIND_ADDRESS=127.0.0.1
PRODUCTION_API_PORT=8000
PRODUCTION_FRONTEND_PORT=3000
NEXT_PUBLIC_API_BASE_URL=https://ipaktoys.ir/api/v1
NEXT_PUBLIC_MEDIA_BASE_URL=https://ipaktoys.ir/media
INTERNAL_API_BASE_URL=http://api:8000/api/v1
```

`NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_MEDIA_BASE_URL`, and Umami's
`NEXT_PUBLIC_*` settings are embedded into the browser bundle at image build
time. Changing them requires rebuilding the frontend image.

`INTERNAL_API_BASE_URL` is server-only and is read by product metadata and
sitemap generation in the standalone Next.js process. It uses the private
Compose network and is not exposed to browser JavaScript. It is intentionally
not supplied while building `next.config.ts`: host Nginx already routes public
`/api/` and `/media/` requests before they reach Next.js, so production browser
rewrites are unnecessary.

Normal storefront registration does not use SMS. `SMS_PROVIDER=disabled`, an
empty Kavenegar key, and `SMS_CONSOLE_ALLOWED=False` are the safe default. The
dormant OTP compatibility endpoints fail closed with a service-unavailable
response. Configure Kavenegar only if those endpoints are deliberately restored
after a separate review.

Keep `DJANGO_SECURE_SSL_REDIRECT=False` during this transition because host
Nginx already owns HTTP-to-HTTPS policy. Set
`DJANGO_TRUST_X_FORWARDED_PROTO=True` only because the audited Nginx removes or
overwrites client-supplied `X-Forwarded-Proto` and sets the actual scheme. This
avoids redirect loops while allowing secure-cookie and request-scheme handling.

Keep `DJANGO_SECURE_HSTS_SECONDS=0`. HSTS, `includeSubDomains`, and preload are
separate long-lived HTTPS-policy decisions and are not enabled by this runtime
transition.

Payment merchant credentials and callback URLs must retain their approved
values. This workflow does not change ZarinPal behavior.

## Host Storage Permissions

The API image runs permanently as UID/GID `10001`. It must write uploaded media
at runtime and write static files only during the explicit `collectstatic` step.
Host Nginx must be able to read both trees.

After verified backups, inspect ownership before changing it:

```bash
stat -c '%u:%g %a %n' \
  /opt/ipaktoys/backend/staticfiles \
  /opt/ipaktoys/backend/media
```

If preparation is required, grant UID/GID 10001 ownership without granting
world write access. The following policy leaves publicly served files readable
by host Nginx while only the application owner can write:

```bash
sudo chown -R 10001:10001 \
  /opt/ipaktoys/backend/staticfiles \
  /opt/ipaktoys/backend/media
sudo find /opt/ipaktoys/backend/staticfiles /opt/ipaktoys/backend/media \
  -type d -exec chmod 0755 {} +
sudo find /opt/ipaktoys/backend/staticfiles /opt/ipaktoys/backend/media \
  -type f -exec chmod 0644 {} +
```

Review an ACL-based alternative if uploaded files must not be world-readable.
In either design, explicitly test the configured Nginx worker user with
`sudo -u www-data test -r <known-file>` and the production API image's write
check in the preflight. Never make either tree world-writable.

## Verified Backups

Run backup commands from Bash with strict pipeline handling. Use a custom-format
PostgreSQL dump so integrity can be inspected without restoring it:

```bash
set -euo pipefail
mkdir -p backups
chmod 700 backups

db_backup="backups/database-before-runtime-$(date -u +%Y%m%dT%H%M%SZ).dump"
media_backup="backups/media-before-runtime-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"

docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec -T db sh -c \
  'exec pg_dump --format=custom --username "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "$db_backup"
test -s "$db_backup"
docker compose --env-file .env.production -f docker-compose.prod.yml \
  exec -T db pg_restore --list < "$db_backup" >/dev/null

tar -C /opt/ipaktoys/backend/media -czf "$media_backup" .
test -s "$media_backup"
tar -tzf "$media_backup" >/dev/null

find /opt/ipaktoys/backend/media -type f | wc -l
du -sb /opt/ipaktoys/backend/media
```

Keep backups outside Git and test restoration in a disposable environment.
Database and media backups must represent an operator-approved compatible
recovery point.

## Mandatory Preflight

Before changing a service, record the current state and tag the current local
application images for rollback:

```bash
set -euo pipefail
readonly expected_release_sha='<reviewed-release-sha>'
readonly db_backup='<verified-database-backup-path>'
readonly media_backup='<verified-media-backup-path>'

git rev-parse HEAD
docker compose --project-name ipaktoys ps
docker inspect ipaktoys-api-1 ipaktoys-frontend-1 > backups/containers-before-runtime.json
docker compose --project-name ipaktoys config > backups/compose-before-runtime.yml
chmod 600 backups/containers-before-runtime.json backups/compose-before-runtime.yml

api_image_id=$(docker inspect --format '{{.Image}}' ipaktoys-api-1)
frontend_image_id=$(docker inspect --format '{{.Image}}' ipaktoys-frontend-1)
docker image tag "$api_image_id" ipaktoys-api:pre-production-runtime
docker image tag "$frontend_image_id" ipaktoys-frontend:pre-production-runtime

scripts/production-preflight.sh \
  .env.production \
  "$expected_release_sha" \
  ipaktoys \
  ipaktoys_postgres_data \
  "$db_backup" \
  "$media_backup" | tee backups/preflight-runtime.log
```

The preflight:

- verifies the exact Git SHA and mode `600` environment file;
- validates the Compose model without printing resolved secrets;
- requires project `ipaktoys` and external volume
  `ipaktoys_postgres_data`;
- fails if the exact existing Docker volume/network cannot be inspected or the
  running database container is mounted to a different volume;
- requires static/media bind paths to exist and loopback-only port bindings;
- validates the custom database dump and media archive;
- records media file count/bytes and static file count;
- builds versioned production images;
- verifies UID/GID 10001 and bind-mount write access;
- runs `check --deploy` and the migration plan in one-off containers;
- does not start, stop, recreate, migrate, seed, or populate any service.

Review every `check --deploy` warning. HSTS and Django SSL redirect warnings are
expected while those policies deliberately remain with Nginx/disabled, but
other warnings require investigation.

## Transition to Gunicorn and Next.js Standalone

Use an approved maintenance window. Keep the existing `db` container running
throughout.

1. Confirm the preflight report, backup validation, current container/image
   record, and Nginx configuration test.
2. Confirm the migration is additive/backward-compatible and review the exact
   plan again:

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml \
     run --rm --no-deps api python manage.py migrate --plan
   ```

3. Only after explicit operator approval, apply required migrations. This is
   never an image entrypoint action:

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml \
     run --rm --no-deps api python manage.py migrate --noinput
   ```

4. Collect static assets into the real host directory:

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml \
     run --rm --no-deps api python manage.py collectstatic --noinput
   ```

5. Recreate only the API with the already-built Gunicorn image, leaving `db`
   untouched, and wait for health:

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml \
     up -d --no-deps --no-build api
   docker compose --env-file .env.production -f docker-compose.prod.yml ps api db
   ```

6. Recreate only the frontend with the already-built standalone image and wait
   for health:

   ```bash
   docker compose --env-file .env.production -f docker-compose.prod.yml \
     up -d --no-deps --no-build frontend
   docker compose --env-file .env.production -f docker-compose.prod.yml ps frontend
   ```

7. Validate host routing without contacting the payment gateway:

   ```bash
   sudo nginx -t
   curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/
   curl --fail --silent --show-error http://127.0.0.1:3000/ >/dev/null
   curl --head http://127.0.0.1:8000/admin/
   curl --head https://ipaktoys.ir/static/<known-static-file>
   curl --head https://ipaktoys.ir/media/<known-media-file>
   curl --head 'https://ipaktoys.ir/api/v1/payments/zarinpal/callback/'
   ```

   A `GET` health response must be `200`; `HEAD` may be `405`. The callback
   request without an authority should only redirect to the safe storefront
   failure page and does not call ZarinPal.

8. Smoke-test the public homepage, product metadata and sitemap, registration,
   login/logout/refresh, cart, checkout, order access, admin static assets, and
   a known uploaded media file. Monitor Gunicorn, Next.js, PostgreSQL, and Nginx
   logs. Do not submit a real payment merely to validate routing.

Gunicorn already binds `0.0.0.0:8000` inside its container, writes access/error
logs to stdout/stderr, handles `SIGTERM`, and has a 40-second Compose stop grace
period for its 30-second graceful timeout. The standalone frontend runs
`node server.js` as UID/GID 10001 with a 30-second stop grace period.

## Rollback

Keep the previous Git SHA, protected resolved Compose configuration, container
inspection output, image IDs/tags, database dump, and media archive until the
maintenance window is formally closed.

For an application-only rollback, first confirm the old application is
compatible with the current schema. Restore the prior image references and
prior reviewed Compose definition, then recreate **only** `api` and `frontend`.
Do not touch `db` or its external volume.

Do not automatically reverse migrations. A database restore is destructive,
discards writes made after the backup, and requires a new maintenance window,
explicit operator approval, stopped application writes, and a coordinated media
restore. Never perform it as an automatic rollback step.

This runtime hardening adds no Django migration and makes no production change
by itself.
