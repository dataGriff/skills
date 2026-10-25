# orders-service

Order management service for the Acme storefront. Python 3.12 (FastAPI) API
with a small Node toolchain for the admin UI bundle.

## Table of contents

- [Setup](#setup)
- [Running](#running)
- [Testing](#testing)
- [Linting and formatting](#linting-and-formatting)
- [Database and migrations](#database-and-migrations)
- [Deploying](#deploying)
- [Architecture](#architecture)
- [Conventions](#conventions)
- [Troubleshooting](#troubleshooting)

## Setup

You need Python 3.12, Node 22 and Postgres 16. Install whichever way you
like (pyenv, nvm, brew, apt ...). Then:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
npm install
cp .env.example .env   # then fill in DATABASE_URL and STRIPE_KEY
```

`DATABASE_URL` must point at a database the app can create tables in.
`STRIPE_KEY` can be the test key from the team 1Password vault.

## Running

```bash
uvicorn orders.app:app --reload --port 8000
npm run dev            # admin UI at http://localhost:5173
```

## Testing

Unit tests:

```bash
pytest tests/unit -q
```

Integration tests need Postgres running (docker compose up -d db first):

```bash
pytest tests/integration -q --maxfail=1
```

Run a single test with `pytest tests/unit/test_pricing.py::test_discount -q`.
Coverage report: `pytest --cov=orders --cov-report=html` then open
`htmlcov/index.html`.

## Linting and formatting

We use ruff for linting and formatting and mypy for types:

```bash
ruff check orders tests
ruff format orders tests
mypy orders
npm run lint           # eslint for the admin UI
```

CI runs all four; run them before pushing or the PR check will fail.

## Database and migrations

Migrations are Alembic. To create one after changing a model:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Never edit a migration that has been merged; write a new one. The
`orders_status` enum is append-only — removing a value breaks replay of the
event log.

## Deploying

`./deploy.sh staging` or `./deploy.sh prod`. Prod deploys need the
`DEPLOY_TOKEN` env var and must happen from `main`. The script builds the
Docker image, pushes it to ECR and updates the ECS service. Rollback is
`./deploy.sh prod --rollback`.

## Architecture

- `orders/api/` — FastAPI routers, one file per resource.
- `orders/domain/` — pure business logic, no IO. Pricing lives in
  `orders/domain/pricing.py`; every discount rule must be a pure function
  with a unit test.
- `orders/repo/` — SQLAlchemy repositories. Only this layer touches the DB.
- `orders/events/` — outbox pattern; every state change writes an event
  row in the same transaction.
- `admin/` — Vite + React admin UI.

Requests flow API → domain → repo. The domain layer must never import from
`orders/api` or `orders/repo`.

## Conventions

- Branch names: `feat/...`, `fix/...`, `chore/...`.
- Commit messages: imperative, under 72 chars, reference the ticket
  (`ORD-123`).
- Every endpoint gets an integration test and an OpenAPI example.
- Money is always `Decimal`, never float. Amounts are stored in minor units.
- Feature flags live in `flags.yaml`; never hardcode a flag check.
- Log with `structlog`; never `print`.

## Troubleshooting

- `psycopg.OperationalError` on startup: the db container is not up, run
  `docker compose up -d db`.
- `alembic` says "target database is not up to date": run
  `alembic upgrade head`.
- Admin UI blank page: `npm run build` then restart the API; it serves the
  bundle from `admin/dist`.
