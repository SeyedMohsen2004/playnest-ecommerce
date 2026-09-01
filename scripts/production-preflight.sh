#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/production-preflight.sh ENV_FILE EXPECTED_GIT_SHA \
  EXPECTED_COMPOSE_PROJECT EXPECTED_POSTGRES_VOLUME DATABASE_BACKUP MEDIA_BACKUP

The database backup must be a PostgreSQL custom-format dump and the media
backup must be a gzip-compressed tar archive. The existing database service must
already be running; this preflight never starts or recreates services.
EOF
  exit 2
}

if [[ $# -ne 6 ]]; then
  usage
fi

readonly ENV_FILE=$1
readonly EXPECTED_GIT_SHA=$2
readonly EXPECTED_COMPOSE_PROJECT=$3
readonly EXPECTED_POSTGRES_VOLUME=$4
readonly DATABASE_BACKUP=$5
readonly MEDIA_BACKUP=$6
readonly REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
readonly COMPOSE_FILE="${REPOSITORY_ROOT}/docker-compose.prod.yml"

cd "$REPOSITORY_ROOT"
umask 077

for command in awk docker du find git mktemp python3 stat tar wc; do
  command -v "$command" >/dev/null || {
    echo "Required command is unavailable: $command" >&2
    exit 1
  }
done

[[ -f "$ENV_FILE" ]] || {
  echo "Production environment file does not exist: $ENV_FILE" >&2
  exit 1
}

env_mode=$(stat -c '%a' "$ENV_FILE")
[[ "$env_mode" == "600" ]] || {
  echo "Production environment file must have mode 600 (found $env_mode)." >&2
  exit 1
}

actual_git_sha=$(git rev-parse HEAD)
[[ "$actual_git_sha" == "$EXPECTED_GIT_SHA" ]] || {
  echo "Git SHA mismatch: expected $EXPECTED_GIT_SHA, found $actual_git_sha." >&2
  exit 1
}

[[ -s "$DATABASE_BACKUP" ]] || {
  echo "Database backup is missing or empty: $DATABASE_BACKUP" >&2
  exit 1
}
[[ -s "$MEDIA_BACKUP" ]] || {
  echo "Media backup is missing or empty: $MEDIA_BACKUP" >&2
  exit 1
}
tar -tzf "$MEDIA_BACKUP" >/dev/null

compose=(
  docker compose
  --env-file "$ENV_FILE"
  -f "$COMPOSE_FILE"
)

config_file=$(mktemp)
trap 'rm -f "$config_file"' EXIT
"${compose[@]}" config --format json > "$config_file"

mapfile -t bind_paths < <(
  python3 - "$config_file" "$EXPECTED_COMPOSE_PROJECT" \
    "$EXPECTED_POSTGRES_VOLUME" <<'PY'
import json
import pathlib
import sys

config_path, expected_project, expected_volume = sys.argv[1:]
with open(config_path, encoding="utf-8") as config_file:
    config = json.load(config_file)

if config.get("name") != expected_project:
    raise SystemExit(
        f"Compose project mismatch: expected {expected_project!r}, "
        f"found {config.get('name')!r}."
    )

postgres_volume = config.get("volumes", {}).get("postgres_data", {})
if not postgres_volume.get("external"):
    raise SystemExit("PostgreSQL volume must resolve as external.")
if postgres_volume.get("name") != expected_volume:
    raise SystemExit(
        f"PostgreSQL volume mismatch: expected {expected_volume!r}, "
        f"found {postgres_volume.get('name')!r}."
    )

services = config.get("services", {})
for service_name in ("api", "frontend"):
    ports = services.get(service_name, {}).get("ports", [])
    if len(ports) != 1 or ports[0].get("host_ip") not in {"127.0.0.1", "::1"}:
        raise SystemExit(f"{service_name} must publish exactly one loopback-only port.")

api_mounts = {
    mount.get("target"): mount
    for mount in services.get("api", {}).get("volumes", [])
}
for target in ("/app/staticfiles", "/app/media"):
    mount = api_mounts.get(target)
    if not mount or mount.get("type") != "bind":
        raise SystemExit(f"{target} must resolve to a host bind mount.")
    source = pathlib.Path(mount["source"])
    if not source.is_absolute():
        raise SystemExit(f"{target} did not resolve to an absolute host path.")
    print(source)
PY
)

[[ ${#bind_paths[@]} -eq 2 ]] || {
  echo "Could not resolve static and media bind paths." >&2
  exit 1
}
readonly STATIC_PATH=${bind_paths[0]}
readonly MEDIA_PATH=${bind_paths[1]}

for path in "$STATIC_PATH" "$MEDIA_PATH"; do
  [[ -d "$path" ]] || {
    echo "Required host directory does not exist: $path" >&2
    exit 1
  }
done

docker volume inspect "$EXPECTED_POSTGRES_VOLUME" >/dev/null
docker network inspect "${EXPECTED_COMPOSE_PROJECT}_default" >/dev/null

readonly DATABASE_CONTAINER="${EXPECTED_COMPOSE_PROJECT}-db-1"
[[ "$(docker inspect --format '{{.State.Running}}' "$DATABASE_CONTAINER")" == "true" ]] || {
  echo "Expected database container is not running: $DATABASE_CONTAINER" >&2
  exit 1
}
mounted_database_volume=$(
  docker inspect --format \
    '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' \
    "$DATABASE_CONTAINER"
)
[[ "$mounted_database_volume" == "$EXPECTED_POSTGRES_VOLUME" ]] || {
  echo "Running database container uses unexpected volume: $mounted_database_volume" >&2
  exit 1
}

# Validate the custom-format dump with the already-running database container.
"${compose[@]}" exec -T db pg_restore --list < "$DATABASE_BACKUP" >/dev/null

media_files=$(find "$MEDIA_PATH" -type f -printf '.' | wc -c)
media_bytes=$(du -sb "$MEDIA_PATH" | awk '{print $1}')
static_files=$(find "$STATIC_PATH" -type f -printf '.' | wc -c)
printf 'Git SHA: %s\n' "$actual_git_sha"
printf 'Compose project: %s\n' "$EXPECTED_COMPOSE_PROJECT"
printf 'PostgreSQL volume: %s\n' "$EXPECTED_POSTGRES_VOLUME"
printf 'Media path: %s (%s files, %s bytes)\n' \
  "$MEDIA_PATH" "$media_files" "$media_bytes"
printf 'Static path: %s (%s files)\n' "$STATIC_PATH" "$static_files"

"${compose[@]}" build api frontend

# One-off containers only: no service is started, recreated, migrated, seeded,
# or populated by this preflight.
"${compose[@]}" run --rm --no-deps --entrypoint sh api -c \
  'test "$(id -u)" = 10001 && test "$(id -g)" = 10001 && test -w /app/staticfiles && test -w /app/media'
"${compose[@]}" run --rm --no-deps api python manage.py check --deploy
"${compose[@]}" run --rm --no-deps api python manage.py migrate --plan

echo "Preflight passed. No production service was started or recreated."
