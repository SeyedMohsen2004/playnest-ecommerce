# Authentication and Browser Sessions

PlayNest uses direct phone-number registration and short-lived JWT access
tokens. The browser never receives a refresh token in JSON: refresh sessions
live only in an HttpOnly cookie, while access tokens exist only in JavaScript
runtime memory.

## Security invariants

- Registration atomically creates a new active, phone-verified account after
  profile, phone, and Django password validation. It never updates an existing
  account and does not invoke SMS or OTP delivery.
- Registration and login issue the same hardened browser session: `{access,
  user}` in JSON and a tracked refresh token only in an HttpOnly cookie.
- The retained OTP compatibility endpoints operate only on eligible historical
  pending registrations and are not used by the storefront registration flow.
- OTP plaintext exists only transiently while calling the delivery adapter. The
  database stores a Django password hash; responses, admin, and logs omit both
  codes and hashes.
- Expired, superseded, failed, uncertain, locked, or used OTPs are ineligible.
  Failed attempts commit before the API returns its generic validation error.
- User-row locks serialize issuance, resend, and verification for one phone.
  An OTP can activate its account once, and resend racing verification has one
  database-ordered outcome. A newer successfully delivered OTP supersedes an
  older candidate, while a newer pending, failed, or uncertain delivery does
  not displace an older eligible OTP.
- Resend cooldown, send-window limits, and bounded login blocking are stored in
  PostgreSQL rather than process-local cache.
- Only active, phone-verified users can receive access or refresh-derived
  access tokens. The legacy direct token endpoint returns HTTP 410.
- Passwords, OTPs, JWTs, provider keys, and complete authentication payloads
  must not be logged.

## Storefront registration

`POST /api/v1/accounts/register/` validates the profile and Django password
rules, stores the password through Django's password hasher, and atomically
creates an active, phone-verified user. It returns HTTP 201 with `{access, user}`
and sets the tracked refresh token only as an HttpOnly cookie. The storefront
does not call an SMS adapter, create a `PhoneOTP`, show a verification page, or
offer a resend action. A duplicate phone number returns a validation error and
cannot change the existing user's profile or password.

## Dormant OTP compatibility

`POST /api/v1/accounts/register/verify/` and
`POST /api/v1/accounts/register/resend/` remain available to avoid an
unnecessary compatibility or migration change. Normal storefront registration
does not create the pending state these endpoints require.

When explicitly used for an eligible historical pending registration, the OTP
service stores only a code hash and calls the SMS adapter outside the database
transaction. A successfully delivered candidate supersedes the prior eligible
OTP under the pending user's row lock.

Provider failure or an uncertain provider response leaves the new OTP unusable
and returns HTTP 503. The console adapter never prints or delivers the code and
therefore always produces an unusable candidate and HTTP 503, even when it is
explicitly enabled for local failure-path testing. Production-like configuration
rejects both `SMS_PROVIDER=console` and `SMS_CONSOLE_ALLOWED=True` at startup and
must use an approved delivery provider.

`POST /api/v1/accounts/register/resend/` requires the phone number only. Both
cooldown and rolling send limits include persisted issuance attempts, so
multiple workers share the same policy. Failed-delivery attempts consume rate
capacity but do not become verifiable.

## Compatibility verification and login controls

Verification locks the pending user and latest eligible OTP. A wrong code
increments `failed_attempts` and commits that update before the view returns an
error. The configured maximum permanently locks that OTP; a resend is required.

Login uses a keyed hash of the phone number as the database throttle identifier.
Failures share a bounded window and temporary block. Successful authentication
removes that identifier's throttle row. Old inactive rows contain no phone
number and may be deleted periodically after the configured failure window and
block duration have elapsed.

## Cookie refresh, logout, and CSRF

Registration, login, and successful compatibility OTP verification return
`{access, user}` and set one non-rotating refresh token cookie. Non-rotation
avoids stale cross-tab responses overwriting newer cookies. Logout blacklists
that refresh token through SimpleJWT and clears the cookie; access tokens remain
valid only for their short configured lifetime.

The cookie is HttpOnly, uses an explicit Path and a same-site `Lax` or `Strict`
policy, has a refresh-lifetime Max-Age, and is Secure whenever
`DJANGO_DEBUG=False`. The CSRF cookie uses the same SameSite policy and is also
required to be Secure outside debug mode. No Domain is widened. Local
configuration uses `localhost` consistently for both frontend and API. The
frontend stores access only in module memory, restores a page reload through
cookie refresh, uses one in-tab refresh promise, and retries a failed
authenticated API request at most once.

A session generation guard rejects stale refresh responses and prevents an
older hydration request from overwriting a newer login or logout. Logout
invalidates local state before the network request, and refresh failure notifies
the React authentication provider immediately. Initial hydration,
invalidation, and logout remove the historical `playnest_access_token` and `playnest_refresh_token` keys
from both browser storage areas without reading their values.

DRF APIViews are CSRF-exempt by default, so registration, verification, resend,
login, refresh, and logout explicitly apply Django `csrf_protect`. The frontend
first calls `GET /api/v1/accounts/csrf/`, then sends the returned token in
`X-CSRFToken` while the matching CSRF cookie and refresh cookie travel with
`credentials: include`. Bearer-authenticated commerce requests remain
independent of CSRF. Credentialed CORS is enabled only for the existing explicit
`CORS_ALLOWED_ORIGINS`; wildcard origins are not used.

## Operational compatibility

The migration preserves users, passwords, and all commerce data. Historical
plaintext OTP rows are converted to unusable failed records and invalidated.
Enabling the cookie session model will require existing browser users to log in
again because earlier browser-visible refresh tokens are deliberately not
accepted from JSON or migrated into cookies.
