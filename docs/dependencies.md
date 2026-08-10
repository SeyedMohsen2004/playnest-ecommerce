# Dependency Management

PlayNest keeps human-reviewed direct constraints separate from generated,
exact lock files. Lock updates are maintenance changes: review their diffs,
advisory impact, compatibility, tests, and production image contents before
merging.

## Python dependency sets

| File | Purpose |
| --- | --- |
| `backend/requirements.in` | Direct application runtime constraints shared by all environments. |
| `backend/requirements-dev.in` | Development, test, quality, compilation, and audit tools. |
| `backend/requirements-prod.in` | Production-only runtime addition (`gunicorn`). |
| `backend/requirements-build.in` | Controlled bootstrap tools used to compile locks and build source distributions. |
| `backend/requirements.txt` | Generated, hash-verified development/test lock. |
| `backend/requirements.prod.txt` | Generated, hash-verified production runtime lock. |
| `backend/requirements-build.txt` | Generated, hash-verified bootstrap lock. |

The input files are maintained by people; the three `.txt` files are generated
with `pip-tools==7.6.0` on Python 3.12. The bootstrap lock pins pip 26.1.2,
setuptools 83.0.0, wheel 0.47.0, and wheel's required packaging dependency.
Pip 26.1.2 is intentional: it contains the fixes required by the current
advisory database and remains compatible with pip-tools 7.6.0. Pip 26.2 removed
an internal API that this compiler release imports. This is a narrowly tested
tooling compatibility constraint, not a claim that application packages require
an older pip.

Kavenegar 1.1.2 is distributed as a source archive. Both lock compilation and
application installation therefore use `--no-build-isolation` after the
bootstrap lock has been installed. Its archive hash, build frontend, setuptools,
wheel, and supporting packaging version are all committed and reviewed; pip is
not allowed to create an isolated environment that downloads unpinned build
requirements.

From `backend/`, create or activate a Python 3.12 environment, then install the
committed bootstrap and development locks:

```bash
python -m pip install --require-hashes -r requirements-build.txt
python -m pip install --require-hashes --no-build-isolation \
  -r requirements.txt
python -m pip check
```

Regenerate every lock with the installed pinned compiler:

```bash
python -m piptools compile --generate-hashes --allow-unsafe \
  --no-build-isolation --resolver=backtracking --strip-extras \
  --output-file=requirements-build.txt requirements-build.in
python -m piptools compile --generate-hashes --no-build-isolation \
  --resolver=backtracking --strip-extras \
  --output-file=requirements.txt requirements-dev.in
python -m piptools compile --generate-hashes --no-build-isolation \
  --resolver=backtracking --strip-extras \
  --output-file=requirements.prod.txt requirements-prod.in
```

Do not edit pins or hashes manually. CI repeats these commands without
`--upgrade` and requires a clean diff for all three generated locks. This
detects input/lock drift while preserving already reviewed compatible pins.
Intentional upgrades require regenerated locks and a reviewed diff.

The production image installs the bootstrap lock only in its builder virtual
environment, installs the production lock with build isolation disabled, runs
`pip check`, and removes pip, setuptools, and wheel from both the copied virtual
environment and the fresh runtime base. Development/test tools such as
pytest, Black, Flake8, pip-tools, and pip-audit are not in the production lock.

## Frontend runtime and lock

Node.js 24 LTS is the supported frontend runtime in CI and every frontend image.
`frontend/.nvmrc` and `package.json` record the same local requirement.
`frontend/package-lock.json` locks the complete npm graph, and CI and both
frontend Dockerfiles use `npm ci`; do not replace it with `npm install` in a
reproducible build path.

Review updates from `frontend/` with Node.js 24:

```bash
npm ci
npm explain postcss
npm explain sharp
npm ls postcss sharp
npm audit
npm audit --omit=dev
npm run lint
npm run build
```

Do not use `npm audit fix --force`. A reported advisory is not permission to
cross a compatibility boundary without focused review.

Next.js 15.5.22 is the latest stable 15.x release at this review point, but it
pins PostCSS 8.4.31 and requests Sharp `^0.34.3`. The root override replaces
those transitive selections with PostCSS 8.5.26 and Sharp 0.35.3. The override
is retained only because Node.js 24 `npm ci`, dependency-tree checks, production
audit, full-audit review, lint, production build, development and standalone
production images, homepage startup, and the Sharp-backed Next.js image
optimizer all passed.
Remove the override once a reviewed Next.js 15 update natively selects patched
versions; do not let it conceal unrelated dependency conflicts.

## Immutable workflow and container references

Every external GitHub Action uses a verified full 40-character commit SHA and
keeps its human-readable release beside the pin as a comment. For an update,
resolve the commit only from the action's official repository and a signed or
GitHub-verified release tag, verify the full SHA through the official repository
metadata, update every use of that release together, and run `actionlint`.
Dependabot's `github-actions` entry proposes future updates; it does not merge
them.

The secret-scanning workflow pins Gitleaks Action 3.0.0 by commit SHA and pins
the downloaded Gitleaks CLI to 8.30.1. Update and verify both independently;
changing the action reference alone does not implicitly authorize a new scanner
binary.

External Dockerfile and Compose bases use `tag@sha256:manifest-list-digest`.
Resolve a replacement from the official image registry, then verify that the
top-level digest represents a multi-platform OCI index rather than a local
image ID or one architecture-specific child. For example:

```bash
docker buildx imagetools inspect python:3.12-slim
docker buildx imagetools inspect node:24-alpine
docker buildx imagetools inspect postgres:16-alpine
```

Update every occurrence, validate both Compose files, and rebuild all affected
images. Dependabot monitors both Dockerfile directories and the root
`docker-compose` ecosystem for digest updates. Patch/minor proposals may be
grouped, major updates remain separate, and nothing is automatically merged.

## Advisory snapshot (2026-08-11)

The prior audit found advisories in direct runtime Pillow 11.3.0 and
development-only Black 25.12.0 and pytest 8.4.2. The focused upgrades to Pillow
12.3.0, Black 26.5.1, and pytest 9.1.1 passed the full backend suite, branch
coverage gate, image-upload validation, Django and OpenAPI checks, formatting,
lint, development and production image builds, and environment consistency
checks. Development and production `pip-audit` runs then reported no known
vulnerabilities.

The production dependency audit, `npm audit --omit=dev`, reports zero known
vulnerabilities for the committed lockfile. The tested Next.js overrides select
PostCSS 8.5.26 and Sharp 0.35.3; PostCSS resolves nanoid 3.3.18 in the current
tree.

The full development dependency audit, `npm audit`, reports two high-severity
tooling-only advisories: brace-expansion 5.0.8 through
`eslint-config-next -> @typescript-eslint/typescript-estree`, and js-yaml 4.3.0
through ESLint configuration tooling. They do not enter the production-only npm
tree. They remain deferred because this maintenance release does not force or
broadly update unrelated lint tooling; they should be reassessed through a
focused, compatible dependency update.

These are point-in-time database results, not proof that the repository or its
dependencies are vulnerability-free. Gitleaks, CodeQL, Dependabot, pip-audit,
and npm audit identify particular risk classes and always require human review.
Repository checks do not deploy to or contact a production host.
