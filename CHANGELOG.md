# Changelog

This changelog follows the principles of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Pending phone registration with hashed, single-use OTPs, delivery state,
  database-backed cooldown/send limits, and concurrency-safe verification.
- Database-backed bounded login throttling, CSRF bootstrap, cookie refresh,
  blacklist-backed logout, and focused authentication architecture tests.
- PostgreSQL concurrency regression coverage for checkout, cancellation,
  payment callbacks, coupon capacity, stock finalization, cart cleanup, and
  shipping updates.
- Per-order coupon reservation records with explicit reserve, consume, and
  release transitions for finite-capacity concurrency safety.
- Focused commerce transaction documentation covering invariants, canonical
  lock ordering, idempotency, and manual-review outcomes.
- Full-history Gitleaks scanning for pull requests, default-branch pushes, and
  manual runs.
- CodeQL analysis for Python and JavaScript/TypeScript on pull requests,
  default-branch pushes, a weekly schedule, and manual runs.
- Weekly Dependabot configuration for Python, npm, GitHub Actions, backend and
  frontend Dockerfiles, and root Docker Compose manifests, with non-major
  grouping and no automatic merge.
- Pull request and portfolio-appropriate issue-template configuration.
- Human-maintained Python dependency inputs and separate generated,
  hash-verified build/bootstrap, development, and production locks.
- Dependency locking and advisory review documentation.

### Changed

- Replaced browser-visible refresh tokens with a non-rotating Secure HttpOnly
  cookie and moved access tokens from localStorage to runtime memory.
- Disabled legacy direct token issuance and body-based refresh, made OTP
  verification mandatory before activation, and added cooldown-aware resend to
  the existing Persian registration UI.
- Moved checkout, cancellation, payment preparation/finalization, and shipping
  mutation orchestration into atomic domain services with deterministic row
  locks and unchanged public endpoint contracts.
- Preserved cart additions made after checkout by snapshotting the original
  cart-line identity and making cleanup idempotent across payment retries.
- Made manual-review reasons sticky, isolated local finalization side effects in
  a savepoint after paid evidence is stored, and classified inventory, coupon,
  reservation, validation, and constraint failures separately.
- Applied a safe no-cart-mutation policy to historical order items without a
  reliable cart-row snapshot and consolidated the unpublished order migrations.
- Updated post-release support, documentation, and repository participation
  wording after the `v1.0.0` publication.
- Hardened CI with least-privilege permissions, per-ref concurrency,
  job timeouts, migration-drift and OpenAPI checks, exact dependency installs,
  and Python environment validation.
- Updated maintained GitHub Action release lines, pinned every action to a
  verified full commit SHA, and aligned frontend package metadata with the
  published `v1.0.0` release.
- Made the development frontend image use the committed lockfile through
  `npm ci`.
- Migrated CI and frontend containers from Node.js 20 to Node.js 24 LTS, with
  matching local version and package-engine metadata.
- Pinned Python 3.12, Node.js 24, and PostgreSQL 16 container bases to verified
  multi-architecture manifest digests while retaining readable tags.
- Installed Kavenegar's source distribution with build isolation disabled after
  installing a dedicated hash-pinned bootstrap toolchain; production removes
  those build tools before the runtime stage.
- Upgraded Pillow 11.3.0 to 12.3.0, Black 25.12.0 to 26.5.1, and pytest 8.4.2
  to 9.1.1 after full backend compatibility validation.
- Updated the development-only transitive `brace-expansion` lock from 1.1.16
  to 1.1.18 to resolve its high-severity denial-of-service advisory.

### Security

- Prevented pre-verification token issuance, plaintext OTP persistence,
  rollback of failed OTP attempts, OTP reuse races, process-local-only login
  controls, browser-readable refresh tokens, and unprotected cookie mutations.
- Prevented Order/Payment lock inversion, coupon-capacity overcommit, repeated
  commerce side effects, paid-payment downgrades, negative stock, and shipping
  mutation races through PostgreSQL-backed transaction invariants.
- Prevented benign duplicate callbacks from clearing non-recoverable manual
  review and prevented handled local constraint failures from erasing verified
  payment evidence or partially committing commerce side effects.
- Resolved the previously reported Python advisories through tested dependency
  upgrades.
- Overrode Next.js 15.5.22's fixed PostCSS 8.4.31 and Sharp 0.34.x transitive
  selections with PostCSS 8.5.25 and Sharp 0.35.3 after clean install, audit,
  lint, build, standalone-server, and image-optimization validation.
- Recorded point-in-time development and production audit results without
  presenting automated scans as proof of complete security.

## [1.0.0] - 2026-07-30

### Added

- Public portfolio context, engineering attribution, and explicit separation
  between the PlayNest implementation and client commercial ownership.
- Architecture, security, contribution, and release documentation.
- Responsible-disclosure guidance and public-repository privacy expectations.
- Django REST Framework ecommerce backend and Persian RTL Next.js/React
  storefront.
- Phone-number/password authentication with JWT access and refresh tokens.
- Product catalog, categories, brands, product media, homepage merchandising,
  wishlist, and reviews.
- Authenticated cart, checkout, customer-owned orders, coupons, and
  shipping-zone pricing.
- ZarinPal payment request, server-side verification callback, and frontend
  success/failure redirects.
- Transactional stock reduction, repeated-callback idempotency, coupon-use
  safeguards, cart finalization, and paid-order manual-review handling.
- Generated and validated OpenAPI contracts with explicit payment and redirect
  response shapes.
- Opt-in production Compose stack with PostgreSQL, Gunicorn, Next.js standalone
  output, non-root containers, persistent static/media/database volumes, and
  health checks.
- 177 backend tests with statement and branch measurement and a 76% combined
  branch-aware CI coverage gate.
- GitHub Actions jobs for backend checks, frontend lint/build, production
  Compose validation, and production image builds.
- Production-oriented Django security settings for explicit hosts, origins,
  cookies, proxy trust, HTTPS redirects, referrer policy, nosniff, and
  deliberately staged HSTS.

### Changed

- Clarified that public repository visibility is for portfolio review and does
  not grant an open-source license or redistribution rights.
- Reworked the main README around verified architecture, behavior, tests,
  coverage, CI, and opt-in production readiness.
- Generalized local product-import examples and removed client-specific dataset
  details and published demo credentials from documentation.
- Corrected stale OTP, mock-payment, deployment, and project-roadmap claims.

### Security

- Customer-facing payment serialization excludes authority values, card hashes,
  raw gateway responses, and sensitive internal verification fields.
- Production secrets and database credentials have no weak Compose fallbacks.
- Migrations and seed data never run automatically in production.
- Uploaded media is persistent and documented as untrusted content.

[Unreleased]: https://github.com/SeyedMohsen2004/playnest-ecommerce/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/SeyedMohsen2004/playnest-ecommerce/releases/tag/v1.0.0
