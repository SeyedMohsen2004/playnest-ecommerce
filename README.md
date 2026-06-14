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
