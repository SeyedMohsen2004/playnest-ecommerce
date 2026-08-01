# Security Policy

## Supported Versions

Security fixes target the latest `v1.0.x` release line and the current default
branch on a best-effort basis. This policy does not establish long-term support
or a guaranteed remediation schedule.

| Version | Supported |
| --- | --- |
| Latest `v1.0.x` release | Yes, best effort |
| Current default branch | Yes, active development |
| Pre-1.0 releases, older commits, or untagged snapshots | No guarantee |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately. Use GitHub private
vulnerability reporting or a repository security advisory when that feature is
available. If no repository-private channel is visible, use the contact options
on the [maintainer's GitHub profile](https://github.com/SeyedMohsen2004) to
request a private reporting channel without disclosing technical details.

Do not open a public issue containing:

- Vulnerability details before remediation is available.
- Credentials, tokens, payment details, personal data, or customer records.
- Exploit payloads, proof-of-concept code, callback authorities, or private
  endpoints.
- Server addresses, privileged paths, logs, backups, or infrastructure details.

Please include a clear description, affected component, observed impact, safe
reproduction conditions, and suggested mitigation in the private report. Allow
reasonable time for triage and remediation before public disclosure.

## Production-Site Permission

Permission to mention or link a production website for portfolio purposes does
not grant permission to security-test it. Do not scan, fuzz, brute-force, probe
privileged routes, create accounts, place orders, trigger payments or SMS,
stress services, bypass access controls, or inspect non-public systems without
separate written authorization from the system owner.

## Secret Management

- Production secrets must be supplied through protected environment or
  secret-management systems and must never be committed.
- Example environment files may contain placeholders only.
- Rotate any credential immediately if it is accidentally exposed; deleting it
  from a later commit is not sufficient.
- Never put private values in `NEXT_PUBLIC_*` variables because they are
  embedded in browser bundles.
- Logs and exception responses must avoid credentials, callback authorities,
  raw provider responses, personal data, and internal infrastructure details.

## Payments and Personal Data

Payment verification must remain server-side. Public serializers and schema
examples must not expose merchant identifiers, payment authorities, card
hashes, raw gateway responses, or private provider messages. Payment,
authentication, authorization, stock, coupon, pricing, shipping, order-state,
and migration changes require focused review and regression tests.

Customer phone numbers, addresses, order records, product-import workbooks,
uploaded media, and operational data are not suitable for public issues,
fixtures, screenshots, documentation, or example datasets. Use synthetic,
reserved data only.

## Dependency Advisories

Dependency advisories are reviewed for affected version, direct or transitive
reachability, production versus development scope, and availability of a
compatible fix. Prefer reproducible patch or minor upgrades. Major upgrades and
forced audit fixes require compatibility review, full tests, and production
build validation.

This policy does not promise a particular response or remediation deadline, but
good-faith private reports will be assessed as promptly as practical.
