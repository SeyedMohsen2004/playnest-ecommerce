# Contributing to PlayNest

This public repository is maintained primarily for portfolio review and
technical evaluation. External contributions are not currently accepted unless
coordinated in advance with the maintainer. This file documents the development
and review standards used for repository changes; it does not grant permission
to use, redistribute, or commercially exploit the code.

## Prerequisites

- Git.
- Docker Engine and Docker Compose v2 for the supported full-stack workflow.
- Python 3.12 and PostgreSQL 16 for native backend development.
- Node.js 24 LTS and npm for native frontend development. The supported local
  version is also recorded in `frontend/.nvmrc` and `package.json`.

Start with [the main README](README.md) and
[architecture documentation](docs/architecture.md).

## Branches

Use a short, descriptive branch name:

```text
feat/short-description
fix/short-description
docs/short-description
test/short-description
chore/short-description
```

Keep each branch limited to one concern. Do not mix formatting, dependency,
infrastructure, and business-behavior changes without a concrete need.

## Commits

Use Conventional Commits:

```text
feat(scope): add a verified capability
fix(scope): correct a confirmed defect
docs(scope): improve public documentation
test(scope): protect meaningful behavior
chore(scope): maintain tooling or infrastructure
```

Do not commit generated build output, coverage artifacts, local environment
files, imported datasets, uploaded media, credentials, or editor state.

## Backend Checks

Run from the repository root with the development stack available:

```bash
docker compose exec api python manage.py check
docker compose exec api python manage.py makemigrations --check --dry-run
docker compose exec api python manage.py spectacular \
  --file /tmp/schema.yml --validate
docker compose exec api pytest \
  --cov --cov-branch --cov-report=term-missing --cov-fail-under=76
docker compose exec api black --check .
docker compose exec api flake8 .
docker compose exec api python -m pip check
```

The coverage configuration measures the five application packages with branch
coverage. CI enforces a combined branch-aware total of at least 76%; do not
disable or bypass the repository coverage configuration.

Schema generation must not introduce drf-spectacular W001 or W002 warnings.
Serializer and endpoint annotations must match actual nullable types, response
bodies, headers, and status codes. Never place private payment data in schema
examples.

## Frontend Checks

From `frontend/`:

```bash
npm ci
npm run lint
npm run build
```

Use the committed lockfile and do not apply forced audit upgrades without
reviewing compatibility and the affected dependency chain.

## Dependency Updates

Python direct constraints live in `backend/requirements.in`,
`requirements-dev.in`, `requirements-prod.in`, and
`requirements-build.in`; the corresponding `.txt` files are generated,
exactly pinned, and hash-verified. Follow
[Dependency Management](docs/dependencies.md) to install the bootstrap lock and
regenerate all three locks with build isolation disabled. Never hand-edit a
generated pin or hash, and always review the build, development, and production
graphs separately. CI regenerates every lock and fails if committed output
drifts from the inputs.

Run `python -m pip check` and `python -m pip_audit` after Python updates. Run
`npm audit` and `npm audit --omit=dev` after frontend updates. Record unresolved
findings and their production relevance; do not hide advisories, force npm
fixes, or cross major versions only to make an audit report green.

Dependabot proposes weekly updates for pip, npm, GitHub Actions, the backend and
frontend Dockerfiles, and root Docker Compose manifests. Patch/minor proposals
may be grouped, but major updates remain separate and no update is automatically
merged.

GitHub Actions must use a verified full commit SHA with the release tag retained
as an adjacent comment. External Dockerfile and Compose base images must retain
a readable tag plus a verified multi-architecture manifest digest. Follow the
verification and update procedure in the dependency documentation; never guess
a SHA or use a local architecture-specific image ID.

## Compose and Production Assets

Validate the local Compose file after relevant changes:

```bash
docker compose config --quiet
```

Production Docker or Compose changes must also validate
`docker-compose.prod.yml`, build both production images, retain non-root
runtimes, preserve explicit migrations and static collection, and avoid source
mounts or fallback secrets. Follow
[the deployment runbook](docs/deployment.md); do not test on a real server
without separate operator authorization.

## Migrations

- Do not create a migration unless a deliberate model change requires one.
- Review generated operations and migration dependencies.
- Include `makemigrations --check --dry-run` and migration tests where relevant.
- Never edit migration history merely to make a check pass.
- Data migrations need forward/rollback analysis, backup implications, and
  explicit operator review.

## Security and Data Policy

- Never commit or paste real secrets, merchant identifiers, SMS credentials,
  database credentials, callback authorities, internal addresses, server access
  details, backups, or private logs.
- Never use customer records, phone numbers, addresses, orders, workbooks,
  images, or analytics as fixtures, screenshots, or examples.
- Use localhost or reserved `.example.invalid` domains and obviously synthetic
  identifiers in tests and documentation.
- Do not probe, authenticate to, scan, fuzz, load-test, place orders on, or
  otherwise test a production deployment without separate written approval.
- Follow [SECURITY.md](SECURITY.md) for responsible disclosure.

## Pull Request Expectations

A pull request should:

1. Explain the problem and the smallest justified solution.
2. Identify behavior, schema, data, security, and deployment impact.
3. List exact validation commands and results.
4. Include meaningful regression tests for behavior changes.
5. Confirm that no secrets, customer data, generated artifacts, or unintended
   migrations are present.
6. Keep documentation and examples accurate.

Payment, authentication, authorization, deployment, stock, coupon, pricing,
shipping, order-state, and migration changes require focused review from a
maintainer familiar with the relevant invariants. Do not merge those changes
based only on a green generic test suite.

Gitleaks and CodeQL run as additional repository checks. Do not add broad secret
scan allowlists, suppress analysis findings without a documented false-positive
review, or describe automated analysis as proof that a change is secure.
