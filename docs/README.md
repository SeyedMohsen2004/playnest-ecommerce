# PlayNest Documentation

PlayNest's public technical documentation is organized around architecture and
an opt-in production deployment workflow.

- [Architecture](architecture.md) describes application boundaries, data flows,
  payment and stock safeguards, and development/production topology.
- [Commerce Transaction Boundaries](commerce-domain.md) documents order and
  payment invariants, canonical row-lock ordering, coupon reservations,
  idempotency, and manual-review behavior.
- [Authentication and Browser Sessions](authentication.md) documents pending
  registration, hashed OTP lifecycle rules, login throttling, HttpOnly refresh
  cookies, logout revocation, and CSRF handling.
- [Production Deployment](deployment.md) documents prerequisites, backups,
  explicit migrations, static collection, health checks, reverse-proxy trust,
  and rollback.
- [Dependency Management](dependencies.md) documents direct inputs, the
  controlled sdist bootstrap, generated hash-pinned locks, Node.js policy,
  immutable Actions and image pins, audits, Dependabot, and current advisory
  decisions.
- [Product Import Data](../backend/import_data/README.md) documents the guarded
  local workbook/image import workflow.
- [Security Policy](../SECURITY.md) explains responsible disclosure and
  sensitive-data expectations.
- [Contributing](../CONTRIBUTING.md) lists required checks and review policy.
- [Changelog](../CHANGELOG.md) records release history and unreleased changes.

Public documentation deliberately omits credentials, customer data, commercial
datasets, private infrastructure, privileged routes, operational logs, backup
locations, and environment-specific server details.
