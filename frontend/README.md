# PlayNest Frontend

The PlayNest storefront is a Persian-first, right-to-left Next.js application
built with the App Router, React, TypeScript, Tailwind CSS, and reusable UI
primitives. It consumes the versioned Django REST API for authentication,
products, cart, checkout, orders, shipping, coupons, and payments.

## Local Setup

```bash
npm ci
cp .env.example .env.local
npm run dev
```

The development server uses `http://localhost:3000` by default. Configure
browser-visible API and media URLs together with the server-side Django API URL:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
NEXT_PUBLIC_MEDIA_BASE_URL=http://localhost:3000/media
INTERNAL_API_BASE_URL=http://localhost:8000/api/v1
```

The `NEXT_PUBLIC_*` variables are public and are embedded at build time. Never
place server-side secrets, merchant identifiers, credentials, or private API
values in them. `INTERNAL_API_BASE_URL` is server-side only and is used by
Next.js for server-side API requests and local proxy rewrites. Docker Compose
overrides it with the internal `http://api:8000/api/v1` service address.

Authentication keeps the access token only in runtime memory. The refresh token
is an HttpOnly API cookie and is never readable by frontend code. Page reloads
bootstrap CSRF and refresh once; registration completes through the OTP step and
the resend control follows the server-provided cooldown. The initial client
hydration and logout actively remove the historical `playnest_access_token` and
`playnest_refresh_token` keys from both `localStorage` and `sessionStorage`
without reading their values. Do not add JWTs, passwords, or OTP values to
browser storage.

Open the frontend as `http://localhost:3000`. Browser API and media requests
remain same-origin through the Next.js proxy, while Django may run on
`http://localhost:8000` when the frontend is started directly. Docker Compose
uses the `api` service hostname internally. Keep the browser origin consistently
on `localhost`; mixing `localhost` and `127.0.0.1` can break the intended
same-site cookie model.

Some visual category and benefit content is static presentation data. Customer
transactions and account state use the Django API; no mock payment gateway is
used.

## Quality

```bash
npm ci
npm run lint
npm run build
```

The production image uses Next.js standalone output and runs the actual
production server as a non-root user. Deployment remains opt-in and is
documented in [the production runbook](../docs/deployment.md).

Client branding, product content, legal copy, and commercial operations are
separate from ownership of the PlayNest engineering implementation.
