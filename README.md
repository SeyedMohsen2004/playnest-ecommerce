# IpakToys Ecommerce

IpakToys is a Django and Next.js ecommerce platform for a board game, puzzle,
intellectual game, and creative games store. It includes authentication,
product catalog, cart, orders, coupons, payments, reviews, wishlist, admin
management, Dockerized PostgreSQL setup, automated tests and CI.

Some internal project names, Docker services, and database defaults still use
the original PlayNest codebase naming for continuity. Customer-facing branding
and demo content use IpakToys.

## Features

- Phone number based authentication
- OTP registration flow
- JWT authentication
- Board game and creative games product catalog
- Categories and brands
- Product images
- Cart management
- Checkout flow
- Orders and order items
- Mock payment gateway flow
- Stock reduction after successful payment
- Coupons and discounts
- Shipping cost calculation
- Wishlist
- Product reviews and ratings
- Improved Django Admin
- Development seed data
- Swagger/OpenAPI documentation
- Dockerized development environment
- PostgreSQL database
- Automated tests
- GitHub Actions CI
- Kavenegar-ready SMS architecture
- Persian-first RTL Next.js frontend

## Tech Stack

| Area | Tools |
| --- | --- |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Infrastructure | Docker, Docker Compose |
| Authentication | SimpleJWT |
| API Docs | drf-spectacular |
| API Utilities | django-filter, django-cors-headers |
| Quality | pytest, black, flake8 |
| CI | GitHub Actions |

## Project Structure

| Path | Description |
| --- | --- |
| `backend/` | Django backend application, API apps, tests, and management commands. |
| `frontend/` | Persian-first RTL Next.js frontend for the customer storefront. |
| `docs/` | Project documentation notes. |
| `docker-compose.yml` | Local development services for API and PostgreSQL. |
| `.env.example` | Example environment variables for development and integrations. |
| `README.md` | Main project documentation. |

## Getting Started

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py seed_data
docker compose exec api python manage.py check
```

The API runs at `http://127.0.0.1:8000`.

## Running Full Stack With Docker

Run the Django API, PostgreSQL database, and Next.js frontend together:

```bash
docker compose up --build -d
docker compose ps
```

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend health | `http://127.0.0.1:8000/api/v1/health/` |
| Swagger docs | `http://127.0.0.1:8000/api/v1/docs/` |

The frontend container uses:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

This URL is intentionally browser-accessible. Do not replace it with
`http://api:8000/api/v1` for frontend browser requests.

If Docker Hub mirror or image download issues occur and images already exist
locally, start the stack without rebuilding:

```bash
docker compose up --no-build -d
```

Common backend commands:

```bash
docker compose exec api python manage.py migrate
docker compose exec api python manage.py seed_data
docker compose exec api pytest
```

## Development Seed Data

Populate an idempotent development catalog:

```bash
docker compose exec api python manage.py seed_data
```

Seed data includes:

- Admin user
- Customer user
- Categories
- Brands
- Board game, puzzle, card game, educational game, and building products
- Coupons

| Account | Phone Number | Password |
| --- | --- | --- |
| Admin | `09120000000` | `AdminPass123!` |
| Customer | `09121111111` | `CustomerPass123!` |

The current coupon model supports percentage and fixed discounts, so a dedicated
`FREESHIP` coupon is not seeded.

## API Documentation

| Resource | URL |
| --- | --- |
| Swagger UI | `http://127.0.0.1:8000/api/v1/docs/` |
| OpenAPI schema | `http://127.0.0.1:8000/api/v1/schema/` |
| Health check | `http://127.0.0.1:8000/api/v1/health/` |

## Testing and Code Quality

Run checks inside the API container:

```bash
docker compose exec api python manage.py check
docker compose exec api pytest
docker compose exec api black --check .
docker compose exec api flake8 .
```

GitHub Actions runs these checks with PostgreSQL on every push and pull request.

## Authentication Flow

1. User registers with phone number, profile details, and password.
2. An OTP code is generated.
3. In development, OTP delivery uses the console SMS provider and prints/logs the
   code in the API container.
4. User verifies the OTP.
5. The account becomes active and phone verified.
6. JWT access and refresh tokens are returned.
7. Login uses phone number and password.

## Payment Flow

1. Checkout creates a pending order and does not reduce stock.
2. Payment request creates or reuses a pending payment for the order.
3. A mock payment gateway is available for development.
4. Successful verification marks the payment as paid.
5. The order becomes paid.
6. Stock is reduced only after successful payment verification.

The payment architecture is designed to be extended to real providers such as
ZarinPal.

## SMS Provider

Development uses the `console` SMS provider. Production can use the Kavenegar
provider.

| Variable | Description |
| --- | --- |
| `SMS_PROVIDER` | `console` for development or `kavenegar` for production delivery. |
| `KAVENEGAR_API_KEY` | Kavenegar API key. |
| `KAVENEGAR_SENDER` | Approved Kavenegar sender line for regular SMS delivery. |
| `KAVENEGAR_VERIFY_TEMPLATE` | Approved Kavenegar VerifyLookup template name. |

Real SMS delivery requires business-owner Kavenegar credentials and an approved
sender line or verification template.

## Product Image Uploads

In development, uploaded product images are stored in `backend/media` and served
from `/media/`. Docker Compose bind-mounts this directory into the API container
so uploaded files persist between container rebuilds.

## Current Status

Backend Core v1 is complete and the frontend storefront is actively connected
to the API for products, authentication, cart, checkout, and payment flow.

Production integrations such as real SMS, real payment gateway, deployment,
domain and SSL will be configured later with business-owner credentials.

## Manual Demo Smoke Routes

Use these routes for a quick customer-demo check after starting the full stack:

| Page | Route |
| --- | --- |
| Home | `/` |
| Products | `/products` |
| Cart | `/cart` |
| Checkout | `/checkout` |
| Mock payment | `/payment/1` |
| Orders | `/account/orders` |
| About | `/about` |
| Contact | `/contact` |
| Terms | `/terms` |
| Privacy | `/privacy` |
| Returns | `/returns` |
| Shipping | `/shipping` |
| Shopping guide | `/shopping-guide` |

## Roadmap

- Complete remaining frontend account and wishlist flows
- Add real ZarinPal integration
- Configure production SMS
- Deploy to production server
- Configure domain, SSL and production environment
- Finalize Enamad/legal pages with business-owner approved text

## Resume Highlights

- RESTful ecommerce backend for board games and creative games
- Dockerized PostgreSQL development environment
- JWT authentication
- OTP architecture
- Payment lifecycle
- Stock consistency after payment
- Admin management
- Test coverage
- CI pipeline
