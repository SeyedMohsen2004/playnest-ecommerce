# PlayNest

Docker-first Django REST API scaffold for a toy ecommerce platform.

## Stack

- Django and Django REST Framework
- PostgreSQL 16
- JWT authentication
- OpenAPI schema and Swagger UI
- pytest, Black, and flake8

## Run

1. Optionally copy `.env.example` to `.env` and change its development values.
2. Build and start the services:

   ```bash
   docker compose up --build
   ```

The API is available at `http://localhost:8000`.

## Development seed data

Populate an idempotent development catalog with users, categories, brands, 20
products with placeholder images, and sample coupons:

```bash
docker compose exec api python manage.py seed_data
```

The coupon model only supports percentage and fixed discounts, so a dedicated
`FREESHIP` coupon is not seeded.

## Product image uploads

In development, uploaded product images are stored in `backend/media` and served
by Django from `/media/`. Docker Compose bind-mounts this directory into the API
container so uploads persist between container rebuilds.

## Development payment flow

Checkout creates a pending order without reducing stock. Request a mock ZarinPal
payment with `POST /api/v1/payments/request/`; the response includes a development
`payment_url`. Confirm it with `POST /api/v1/payments/verify/` using the returned
authority and `status: "OK"`. Successful verification marks the order paid and
reduces stock atomically.

## SMS providers

Development uses `SMS_PROVIDER=console`, which prints registration OTP codes to
the API console without contacting an external service.

For production Kavenegar delivery, set `SMS_PROVIDER=kavenegar` and provide
`KAVENEGAR_API_KEY`. Set `KAVENEGAR_VERIFY_TEMPLATE` to use Kavenegar
VerifyLookup template delivery, or provide `KAVENEGAR_SENDER` for regular SMS
delivery. Real delivery requires a valid Kavenegar API key and an approved
sender line or verification template.

## API endpoints

- Health: `GET /api/v1/health/`
- Swagger UI: `GET /api/v1/docs/`
- OpenAPI schema: `GET /api/v1/schema/`
- JWT token: `POST /api/v1/auth/token/`
- JWT refresh: `POST /api/v1/auth/token/refresh/`

## Quality checks

Run checks inside the API container:

```bash
docker compose run --rm api pytest
docker compose run --rm api black --check .
docker compose run --rm api flake8 .
```

## Continuous integration

GitHub Actions runs the Django system check, PostgreSQL-backed pytest suite,
Black formatting check, and flake8 linting on every push and pull request.
