# Agent guide — payments-gateway

Go 1.23 service that authorises card payments and forwards captures to the
PSP. This file is what agents load first; keep it current.

## Ground rules

1. Run `make help` first and reuse the targets it lists; add a target to
   the Makefile rather than a one-off command.
2. Run `make ci` (lint + tests) before you say a change is done. CI runs
   the same target.
3. Never edit anything under `gen/` — it is generated from `proto/` by
   `make proto`.
4. Money is `int64` minor units, never float. Currency travels with every
   amount as an ISO 4217 code.
5. Every write endpoint takes an `Idempotency-Key` header; the handler
   must return the stored response on a repeat key.

## Commands

| Target            | Does                                             |
| ----------------- | ------------------------------------------------ |
| `make build`      | compile to `bin/gateway`                         |
| `make test`       | unit tests; `make test PKG=./internal/capture`   |
| `make lint`       | golangci-lint with the repo config               |
| `make ci`         | lint + test — what CI runs                       |
| `make proto`      | regenerate `gen/` from `proto/`                  |
| `make migrate`    | apply SQL migrations in `migrations/`            |
| `make run`        | start on :8080 against docker-compose services   |

## Layout

```
cmd/gateway/      main
internal/auth/    PSP authorisation client
internal/capture/ capture + settlement
internal/ledger/  double-entry ledger; every capture writes two rows
gen/              generated protobuf (do not edit)
migrations/       goose SQL migrations, numbered
docs/             longer docs
```

## Conventions

- Branches `pg-<ticket>-<slug>`; commits imperative, under 72 chars.
- Errors wrap with `fmt.Errorf("...: %w", err)`; never swallow an error.
- Table-driven tests; fixtures in `internal/testdata/`.
- New migrations are additive; never edit a merged migration.
