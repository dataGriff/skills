# CLAUDE.md — instructions for Claude

You are working in `notify`, a TypeScript notification service (Node 22,
pnpm, Fastify, Prisma on Postgres, BullMQ on Redis). Read this whole file
before doing anything.

## Setup

- `pnpm install` then `pnpm prisma generate`.
- Copy `.env.example` to `.env`. `REDIS_URL` and `DATABASE_URL` are required.
  Never commit `.env`.
- Start dependencies with `docker compose up -d`.

## Commands

- Dev server: `pnpm dev` (tsx watch on `src/server.ts`).
- Tests: `pnpm test` runs vitest. `pnpm test -- src/channels/email.test.ts`
  runs one file. Integration tests are in `test/integration` and need
  Postgres + Redis: `pnpm test:integration`.
- Lint: `pnpm lint` (eslint + prettier check). Fix with `pnpm lint:fix`.
- Typecheck: `pnpm typecheck` (tsc --noEmit).
- Build: `pnpm build` (tsup to `dist/`).
- Migrations: `pnpm prisma migrate dev --name <name>`; in prod
  `pnpm prisma migrate deploy`.
- Load test: `pnpm loadtest` (k6, needs `K6_API_KEY`).
- Generate an SDK client: `pnpm gen:sdk` (reads `openapi.yaml`).

Always run `pnpm lint && pnpm typecheck && pnpm test` before you say a task
is done.

## Architecture

- `src/channels/` — one module per delivery channel (email, sms, push,
  webhook). Each exports `send(message): Promise<DeliveryResult>` and a
  `validate(payload)` schema (zod).
- `src/queue/` — BullMQ producers and workers. Every job type is registered
  in `src/queue/registry.ts`; a job type without a registry entry is a bug.
- `src/templates/` — MJML email templates compiled at build time. Run
  `pnpm build:templates` after editing one.
- `src/api/` — Fastify routes. Routes validate with the channel's zod
  schema and never contain business logic.
- `prisma/schema.prisma` — the schema. Every model has `createdAt` and
  `updatedAt`.

Message flow: API → validate → enqueue → worker → channel.send → record
delivery in `deliveries` table → emit `delivery.completed` event.

## Rules

- Retries: channel `send` must be idempotent; the worker retries with
  exponential backoff (max 5). Never implement retries inside a channel.
- Rate limits per channel live in `config/limits.yaml`. Never hardcode a
  limit.
- PII: never log message bodies or recipient addresses. Log the message id
  and channel only. There is a lint rule for this; do not disable it.
- Feature flags come from `src/flags.ts` (LaunchDarkly). Never check a flag
  by reading an env var.
- Timestamps are stored in UTC and rendered in the recipient's timezone
  from `users.timezone`.
- Webhook signing uses HMAC-SHA256 with the per-customer secret in
  `customers.webhook_secret`; never send an unsigned webhook.
- Every new channel needs: a module in `src/channels/`, a registry entry, a
  template directory, an integration test, and an entry in
  `docs/channels.md`.

## Testing conventions

- Unit tests sit next to the code (`foo.test.ts`).
- Use the factories in `test/factories/`; never hand-build a `Message`.
- Integration tests truncate tables in `beforeEach` via `test/db.ts`.
- Snapshot tests are only for rendered templates.

## Git

- Branch from `main`, name `nt-<ticket>-<slug>`.
- Conventional commits (`feat:`, `fix:`, `chore:`), scope optional.
- Squash-merge; the PR title becomes the commit message.
- CI must be green; do not bypass branch protection.

## Deployment

- `main` auto-deploys to staging via GitHub Actions
  (`.github/workflows/deploy.yml`).
- Production is a manual `workflow_dispatch` of the same workflow with
  `environment=production`; needs an approval from the on-call.
- Rollback: re-run the previous successful production deploy.

## Troubleshooting

- `PrismaClientInitializationError`: Postgres is not up, or `DATABASE_URL`
  is wrong.
- Jobs stuck in `waiting`: the worker is not running (`pnpm worker`) or
  Redis is down.
- Emails render blank: templates were edited without `pnpm build:templates`.
- `429` from the SMS provider: check `config/limits.yaml` against the
  provider's plan.

## Things Claude gets wrong here

- Do not add `any` types; the lint rule fails CI.
- Do not create new top-level directories; ask first.
- Do not edit generated files under `src/generated/`.
- Do not run `prisma migrate reset` — it drops the database.

## Channels reference

### email
Provider: Postmark. Config: `POSTMARK_TOKEN`, `EMAIL_FROM`. Templates are
MJML under `src/templates/email/`; the compiled HTML is committed under
`src/templates/compiled/` and must be regenerated with `pnpm build:templates`
in the same PR as the template change. Bounces arrive on
`POST /webhooks/postmark` and mark the recipient `suppressed` in `users`.
Attachments are limited to 10 MB total; larger ones are uploaded to S3 and
linked. Plain-text alternatives are generated automatically from the MJML;
do not hand-write them.

### sms
Provider: Twilio. Config: `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM`.
Messages over 160 GSM-7 characters are segmented and billed per segment;
`validate` warns above 3 segments and rejects above 10. Delivery receipts
arrive on `POST /webhooks/twilio`. Short links use the `lnk.notify.io`
domain via `src/links.ts`; never paste raw URLs into SMS bodies.

### push
Providers: APNs (iOS) and FCM (Android). Config: `APNS_KEY_ID`,
`APNS_TEAM_ID`, `APNS_KEY_PATH`, `FCM_SERVICE_ACCOUNT`. Device tokens live
in `devices`; a `410` from APNs or `UNREGISTERED` from FCM deletes the
device row. Payload limit is 4 KB; the `validate` schema enforces it.
Silent pushes (`content-available`) are only allowed for the `sync` job
type.

### webhook
Customer-configured URLs in `customers.webhook_url`. Signed with
HMAC-SHA256 over the raw body using `customers.webhook_secret`, sent in the
`X-Notify-Signature` header as `sha256=<hex>`. Timeout 10 s; a non-2xx is
retried by the worker per the standard backoff. After 5 failures the
customer's webhook is disabled and `webhook.disabled` is emitted.

## API reference

All routes are under `/v1` and require a bearer API key (`api_keys` table,
hashed with argon2). Rate limit: 600 requests/minute per key, enforced in
`src/api/rateLimit.ts` using Redis.

- `POST /v1/messages` — enqueue a message. Body is the channel's zod
  schema plus `channel`, `to`, and optional `scheduleAt` (ISO 8601, UTC).
  Returns `202` with `{ id }`.
- `GET /v1/messages/:id` — status and delivery attempts.
- `POST /v1/messages/:id/cancel` — cancels a scheduled message; `409` if it
  has already been sent.
- `GET /v1/deliveries?since=` — paginated with an opaque `cursor`; page
  size 100.
- `POST /v1/customers/:id/webhook` — set or rotate the webhook URL and
  secret. Rotation keeps the old secret valid for 24 hours.
- `GET /healthz` and `GET /readyz` — no auth; readiness checks Postgres and
  Redis.

Errors follow RFC 9457 problem details; the `type` URI is
`https://notify.io/errors/<code>`. Add new codes to `src/api/errors.ts` and
`docs/errors.md` together.

## Observability

- Metrics: Prometheus on `:9464/metrics`. Every channel exports
  `notify_send_total{channel,status}` and `notify_send_duration_seconds`.
- Tracing: OpenTelemetry; the trace id is propagated into job data as
  `traceparent` so worker spans join the API span.
- Alerts live in `ops/alerts.yaml`; a new channel needs a delivery failure
  rate alert there.

## Local data

`pnpm seed` loads `test/seed/*.json` (customers, api keys, users, devices)
into the local database. The seeded API key is `nt_test_local`. Re-run the
seed after `pnpm prisma migrate dev` if tables were recreated.
