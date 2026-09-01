import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const [compose, backendDockerfile, frontendDockerfile, apiClient, sitemap] =
  await Promise.all([
    readFile(new URL("../docker-compose.prod.yml", import.meta.url), "utf8"),
    readFile(new URL("../backend/Dockerfile.prod", import.meta.url), "utf8"),
    readFile(new URL("./Dockerfile.prod", import.meta.url), "utf8"),
    readFile(new URL("./lib/api/client.ts", import.meta.url), "utf8"),
    readFile(new URL("./app/sitemap.ts", import.meta.url), "utf8"),
  ]);

test("production database and host content mounts fail closed", () => {
  assert.match(
    compose,
    /name: \$\{PRODUCTION_POSTGRES_VOLUME_NAME:-[^}]+\}\s+external: true/u,
  );
  assert.match(compose, /source: \$\{PRODUCTION_STATIC_PATH/u);
  assert.match(compose, /source: \$\{PRODUCTION_MEDIA_PATH/u);
  assert.equal((compose.match(/create_host_path: false/gu) || []).length, 2);
});

test("production containers do not mutate data or assets on startup", () => {
  assert.match(backendDockerfile, /gunicorn config\.wsgi:application/u);
  assert.doesNotMatch(
    backendDockerfile,
    /manage\.py (?:migrate|collectstatic)|seed_data/u,
  );
});

test("public media is supplied at build time and internal API stays server-only", () => {
  assert.match(frontendDockerfile, /ARG NEXT_PUBLIC_MEDIA_BASE_URL/u);
  assert.match(
    compose,
    /INTERNAL_API_BASE_URL: \$\{INTERNAL_API_BASE_URL:-http:\/\/api:8000\/api\/v1\}/u,
  );
  assert.match(apiClient, /process\.env\.INTERNAL_API_BASE_URL/u);
  assert.match(sitemap, /process\.env\.INTERNAL_API_BASE_URL/u);
  assert.doesNotMatch(frontendDockerfile, /ARG INTERNAL_API_BASE_URL/u);
});
