# Architecture

## Overview

It is worth noting, before going into any detail, that the architecture of
ledger-api is deliberately boring. Basically, requests flow API → service →
repository → Postgres. There is nothing clever going on, and that is the
point: a ledger has to be trustworthy above all, so we have, in order to keep
it that way, resisted every temptation to add layers.

## Layers

- `api/` — FastAPI routers. They validate input with pydantic models and call
  a service. They contain no business logic.
- `services/` — business logic. The ledger service is the only code that
  writes ledger rows.
- `repositories/` — SQLAlchemy. Only this layer touches the database.

## Identifiers

IDs are UUIDv7 (ADR-3), because sort order matters for the ledger: entries
must be returned in insertion order without a separate sequence, and
UUIDv7's time prefix gives that for free.

## Double entry

Every capture writes two ledger rows in one transaction, a debit and a
credit, and the service refuses to commit if they do not balance. This
invariant is checked in `services/ledger.py` and in the integration tests.

## How we got here

Originally, as you may know, the service was a single Flask module with SQL
strings inline. We moved to the layered layout in v1.5, after a bug where a
handler wrote to the ledger table directly and bypassed the balance check.
Previously the repository layer used raw psycopg; we switched to SQLAlchemy
in v1.9 mostly so that the migrations and the models would live together.
There was also a period where we tried an event-sourced design, which we
abandoned after two months because replay times were unacceptable.
