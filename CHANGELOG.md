# Changelog

This changelog follows the principles of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

No unreleased changes.

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
