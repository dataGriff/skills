# Local setup

## Prerequisites

You will need Python 3.12 and Postgres 16. It is worth noting that other
versions may work, but they are not what CI runs, so please note that you
are on your own with them.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill in `DATABASE_URL` in `.env`. Never commit `.env`; secrets come from
Vault.

## Database

Start Postgres with `docker compose up -d db`, then apply migrations with
`alembic upgrade head`.

## Migration diary (March 2024)

- 2024-03-04: started the move from Flask to FastAPI behind the `NEW_HTTP`
  flag. Only `/health` was ported on day one.
- 2024-03-11: ported the ledger endpoints. Found that the old validation
  layer accepted negative amounts; fixed in the new one.
- 2024-03-19: flag enabled in staging. Two integration tests had to be
  rewritten because they asserted on Flask error bodies.
- 2024-03-27: flag enabled in production. No incidents.
- 2024-04-02: Flask code path deleted.

## Troubleshooting

- `psycopg.OperationalError` on startup: Postgres is not up; run
  `docker compose up -d db`.
- `alembic` says the database is not up to date: run `alembic upgrade head`.
