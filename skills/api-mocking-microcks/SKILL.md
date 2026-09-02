---
name: api-mocking-microcks
description: >-
  Mock and contract-test REST (OpenAPI) and event-driven (AsyncAPI) APIs with
  Microcks (microcks.io): spin up a local mock server, author specs whose
  examples become live mocks, dispatch different responses per request, mock
  Kafka/WebSocket/MQTT events, and wire mocks into tests and CI with
  Testcontainers or microcks-cli. Use when the user mentions Microcks, wants
  to mock an API or simulate a backend/broker from an OpenAPI or AsyncAPI
  spec, needs fake endpoints or sample events for local development or
  integration tests, or wants contract testing of an implementation against
  its spec. Also use when adding examples/x-microcks extensions to a spec so
  it mocks well.
---

# API mocking with Microcks

Microcks (CNCF) turns API specifications into live mocks and contract tests.
One instance handles both synchronous APIs (OpenAPI/REST, also GraphQL, gRPC,
SOAP) and asynchronous ones (AsyncAPI over Kafka, WebSocket, MQTT, AMQP,
NATS, …). As of 2026 the current release line is 1.14.x/1.15.x; prefer a
pinned recent tag over `latest` for reproducibility.

The core mental model:

1. **Import artifacts.** A spec file (OpenAPI, AsyncAPI, Postman collection,
   APIExamples overlay…) is imported as a *main* or *secondary* artifact.
   The main artifact defines the API contract; secondary artifacts layer
   extra examples or metadata onto it.
2. **Examples become mocks.** Microcks does not fabricate data — it serves
   the *named examples* in the spec. An API with no examples yields empty
   mocks, so authoring good examples is most of the work.
3. **Identity is `info.title` + `info.version`.** Mock URLs and CLI/test
   commands reference the API by that name:version pair. Renaming or
   re-versioning the spec creates a *new* API in Microcks.
4. **The same spec drives contract tests.** Point Microcks at a real
   implementation and it replays requests/validates responses (or consumed
   events) against the schema.

## Quick start (local mock server)

The uber image is a single container, no auth, ideal for local dev:

```bash
docker run -d --name microcks -p 8585:8080 quay.io/microcks/microcks-uber:1.14.0
# UI at http://localhost:8585 — mocks served on the same port

# Import a spec as the main artifact (no CLI needed):
curl -F "file=@order-api.yaml" -F "mainArtifact=true" \
  http://localhost:8585/api/artifact/upload
```

Mock endpoints follow a fixed pattern (spaces in the API name are written
as `+`, the form the Microcks UI shows; `%20` works too):

```
REST:      http://localhost:8585/rest/{API name}/{version}/{path}
GraphQL:   http://localhost:8585/graphql/{API name}/{version}
SOAP:      http://localhost:8585/soap/{API name}/{version}
WebSocket: ws://localhost:8585/api/ws/{API name}/{version}/{channel}
```

e.g. `curl http://localhost:8585/rest/Order+API/1.0/orders/123`. The UI's
API detail page lists the exact endpoint for every operation — check there
rather than guessing encodings.

For full installs (Keycloak auth, Kafka async stack, Kubernetes/Helm) and
event mocking, see the references below.

## Workflow

1. **Author or fix the spec for mockability.** Add named examples to every
   operation and pair request/response examples by name. This is the step
   that makes or breaks the mocks — open
   [references/openapi-mocking.md](references/openapi-mocking.md) for REST
   conventions (examples, `x-microcks-refs`, `x-microcks-operation`,
   APIExamples overlays) or
   [references/asyncapi-mocking.md](references/asyncapi-mocking.md) for
   event conventions and enabling async support (Kafka, WebSocket, …).
2. **Run Microcks and import.** Uber image + `curl` upload above, or
   `microcks-cli import`, or Testcontainers inside a test suite.
3. **Exercise the mocks.** Curl the endpoints; verify each request variant
   returns the intended example. If every request returns the same response
   or a 400, the dispatcher isn't matching — see
   [references/dispatchers-and-templating.md](references/dispatchers-and-templating.md)
   to pick a dispatcher (URI_PARTS, JSON_BODY, SCRIPT, FALLBACK, …) and to
   make responses dynamic with `{{ }}` template functions.
4. **Automate.** Embed mocks in unit/integration tests with Testcontainers
   (Java, Node, Go, Python, .NET), or run `microcks-cli import`/`test` in
   CI to keep mocks fresh and contract-test deployed implementations:
   [references/automation-and-testing.md](references/automation-and-testing.md).

## Practical notes

- **Import fails or API shows zero operations** → the spec is invalid or
  lacks `info.title`/`info.version`. Lint it first; Microcks skips
  operations it cannot parse.
- **Mock returns a 400 "dispatch criteria" error** → no example matches the
  request. Either add an example for that variant or set a `FALLBACK`
  dispatcher so unmatched requests get a default response.
- **Multiple example files for one API** → import the spec with
  `mainArtifact=true` and each extra file (APIExamples overlay, Postman
  collection) with `mainArtifact=false`. Same `info.title` + version, or
  they land on separate APIs.
- **Don't hand-craft mock URLs in app config** — inject the base endpoint
  (Testcontainers exposes `getRestMockEndpoint(...)`) so tests survive port
  changes.
- Microcks never mutates state: POST/PUT/DELETE mocks return their example
  responses but store nothing. For stateful behavior use a `SCRIPT`
  dispatcher or accept stateless semantics in tests.

## References

- [references/openapi-mocking.md](references/openapi-mocking.md) — authoring
  OpenAPI specs that mock well: named examples, request/response pairing,
  `x-microcks-refs`, `x-microcks-operation`, APIExamples/APIMetadata
  overlays, delays.
- [references/asyncapi-mocking.md](references/asyncapi-mocking.md) —
  AsyncAPI 2.x/3.x conventions, enabling the async minion, per-protocol
  endpoints (Kafka, WebSocket, MQTT…), event frequency, async contract
  tests.
- [references/dispatchers-and-templating.md](references/dispatchers-and-templating.md)
  — dispatcher catalog with rules syntax, and template functions for dynamic
  responses (`guid()`, `now()`, `randomInt()`, request-derived values).
- [references/automation-and-testing.md](references/automation-and-testing.md)
  — full/docker-compose installs, microcks-cli, GitHub Actions, importer
  scheduling, Testcontainers per language, contract-test runners.
