# ledger-api

## Introduction

As you may know, ledger-api is basically the service that is responsible for
recording every financial movement in the Acme platform. It is worth noting
that it was designed, in order to be as reliable as possible, around an
append-only ledger, which is to say that rows are never updated in place.
Please note that this README is intended to be the first thing you read, and
needless to say, it tries to cover everything you might want to know.

Licensed under MIT — see LICENSE.

## Getting started

In order to get started you will simply need Python 3.12 and Postgres 16.
Basically the steps are as follows. First of all, create a virtual environment,
and then install the package in editable mode with the development extras,
which will just pull in everything you need:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Please note that you should then fill in `DATABASE_URL` in `.env`. Never
commit `.env`; secrets come from Vault, and the `.env.example` file only
contains placeholders.

The service listens on `PORT=8080` by default. To run it locally:

```bash
make run
```

## Running the tests

It is worth noting that we have both unit and integration tests. Basically,
`make test` runs the whole suite, and it is, needless to say, what CI runs,
so you should run it before you push. Linting is done with `ruff`, which
`make lint` wraps.

## Database

Migrations are Alembic. After changing a model you will want to generate a
migration and then apply it with `alembic upgrade head`. Please note that a
migration that has been merged is never edited; write a new one instead.

## History

Previously we used Flask for the HTTP layer, with a hand-rolled request
validation layer that, it is worth noting, caused a number of production
incidents in 2022 because validation errors were returned as 500s. As of v2
we switched to FastAPI, which validates with pydantic models and returns
422s. The switch took about three months and was done behind a feature
flag; the Flask code path was removed in v2.3. Originally the ledger table
was called `transactions`, which we renamed to `ledger_entries` in v1.8
because "transaction" was ambiguous with database transactions. We no longer
support the v1 API at all.

## Why we chose Postgres

When the project started there was a long discussion about whether to use
Postgres, MySQL or DynamoDB. In the end we chose Postgres, because we
needed transactional guarantees across multiple rows for double-entry
bookkeeping, and because the team had operated it before. DynamoDB was
rejected because conditional writes across items were awkward at the time,
and MySQL was rejected mostly on familiarity grounds. This decision was
revisited in 2023 and reaffirmed.

## Architecture

See docs/architecture.md, which goes into a lot more detail. The short
version is that requests flow API → service → repository → Postgres, and
every write goes through the ledger service so that double-entry invariants
hold.

## Contributing

See CONTRIBUTING.md. Please note that pull requests need a green `make test`
and a reviewer from the ledger team.
