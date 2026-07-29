# PlayNest Documentation

PlayNest's public technical documentation is organized around architecture and
an opt-in production deployment workflow.

- [Architecture](architecture.md) describes application boundaries, data flows,
  payment and stock safeguards, and development/production topology.
- [Production Deployment](deployment.md) documents prerequisites, backups,
  explicit migrations, static collection, health checks, reverse-proxy trust,
  and rollback.
- [Product Import Data](../backend/import_data/README.md) documents the guarded
  local workbook/image import workflow.
- [Security Policy](../SECURITY.md) explains responsible disclosure and
  sensitive-data expectations.
- [Contributing](../CONTRIBUTING.md) lists required checks and review policy.
- [Changelog](../CHANGELOG.md) records unreleased and prepared release notes.

Public documentation deliberately omits credentials, customer data, commercial
datasets, private infrastructure, privileged routes, operational logs, backup
locations, and environment-specific server details.
