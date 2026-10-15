---
name: microcks
description: >-
  Mock and contract-test APIs from their specs with Microcks: run a local
  mock server, author OpenAPI/AsyncAPI examples that become live mocks,
  dispatch responses per request, mock Kafka/WebSocket/MQTT events, and
  verify a running implementation conforms to its spec with schema
  runners, from Testcontainers in tests or the microcks CLI and GitHub
  Actions in CI. Use when the user mentions Microcks, wants to mock an API
  or simulate a backend or broker from a spec, needs fake endpoints or
  sample events, is adding examples or x-microcks extensions, or wants
  contract, conformance or provider testing. Writing the spec itself is
  openapi-authoring or asyncapi-authoring.
---

# Microcks: mocks and contract tests from one spec

Microcks (CNCF) turns API specifications into live mocks and checks real
implementations against them. One instance handles synchronous APIs
(OpenAPI/REST, GraphQL, gRPC, SOAP) and asynchronous ones (AsyncAPI over
Kafka, WebSocket, MQTT, AMQP, NATS, …). As of 2026 the release line is
1.14.x/1.15.x; pin a recent tag rather than `latest`.

The mental model, which every task below relies on:

1. **Import artifacts.** A spec (OpenAPI, AsyncAPI, Postman collection,
   APIExamples overlay…) is imported as a *main* or *secondary* artifact.
   The main artifact defines the contract; secondary ones layer extra
   examples, metadata or test scripts onto it.
2. **Examples are the contract's data.** Microcks never fabricates data:
   it serves the spec's *named examples* as mocks and replays them as test
   cases. No examples, no mocks and nothing to test, so authoring good
   examples is most of the work.
3. **Identity is `info.title` + `info.version`.** Mock URLs and tests
   reference the API as `Name:version`. Renaming or re-versioning the spec
   creates a *new* API; a mismatch is the usual "service not found".
4. **One spec, two sides.** Consumers call the mocks; the provider is
   tested by replaying the same examples against its real endpoint.

## Quick start (local server)

```bash
docker run -d --name microcks -p 8585:8080 quay.io/microcks/microcks-uber:1.14.0
# UI and mocks on http://localhost:8585, no auth
curl -F "file=@order-api.yaml" -F "mainArtifact=true" \
  http://localhost:8585/api/artifact/upload
```

Mock endpoints follow a fixed pattern (spaces in the API name become `+`,
as the UI shows; `%20` works too):

```
REST:      http://localhost:8585/rest/{API name}/{version}/{path}
GraphQL:   http://localhost:8585/graphql/{API name}/{version}
SOAP:      http://localhost:8585/soap/{API name}/{version}
WebSocket: ws://localhost:8585/api/ws/{API name}/{version}/{channel}
```

The UI's API page lists the exact endpoint per operation; check there
rather than guessing encodings.

## Mocking an API

1. **Make the spec mockable.** Give every operation named examples and
   pair request and response examples by name: the same name on the
   parameter or body example and on the response example that answers
   it, with every required parameter valued in each. This step makes or
   breaks the mocks. Open
   [references/openapi-mocking.md](references/openapi-mocking.md) when you
   need more than that pairing rule (body matching, `x-microcks-refs`,
   overlays for specs you cannot edit), and
   [references/asyncapi-mocking.md](references/asyncapi-mocking.md) when
   the API is event-driven (message examples, publish frequency, broker
   endpoints).
2. **Import and exercise.** Curl each request variant and check it returns
   the intended example. If every request gets the same response, or a
   400, the dispatcher is not matching: open
   [references/dispatchers-and-templating.md](references/dispatchers-and-templating.md)
   when you need to pick a dispatcher (URI_PARTS, JSON_BODY, SCRIPT,
   FALLBACK, …) or make responses dynamic with `{{ }}` templates.
3. **Inject, don't hard-code.** Apps and tests take the mock base URL from
   config or from Testcontainers (`getRestMockEndpoint(...)`), so they
   survive port and name changes.

## Contract-testing an implementation

Give Microcks the service (`"Name:version"`), the implementation's
`testEndpoint` (its base URL, not Microcks'; Microcks appends each
operation's path) and a runner:

| Runner             | For            | Validates                            |
| ------------------ | -------------- | ------------------------------------ |
| `HTTP`             | REST, SOAP     | endpoint answers sensibly            |
| `OPEN_API_SCHEMA`  | REST           | status + response schema vs OpenAPI  |
| `ASYNC_API_SCHEMA` | events         | captured messages vs AsyncAPI schema |
| `GRPC_PROTOBUF`    | gRPC           | responses vs Protobuf schema         |
| `GRAPHQL_SCHEMA`   | GraphQL        | responses vs GraphQL schema          |
| `POSTMAN`          | REST/SOAP/GQL  | Postman collection test scripts      |
| `SOAP` / `SOAP_UI` | SOAP           | XSD schemas / SoapUI assertions      |

Default to the `*_SCHEMA` runner for the protocol; use `POSTMAN` when
business assertions beyond schema shape are needed (import the collection
as a secondary artifact). Use these ids exactly: they are the enum the API
expects, and a near miss such as `OPENAPI_SCHEMA` fails only at runtime.

```bash
microcks test 'Order API:1.0' http://localhost:3000 OPEN_API_SCHEMA \
  --microcksURL=http://localhost:8585/api/ --waitFor=10sec
# no server at all: ephemeral container from a local spec
microcks test --dry-run --artifact ./openapi.yaml \
  'Order API:1.0' http://localhost:3000 OPEN_API_SCHEMA
```

Exit code 0 means the contract holds and 1 means violations, so the
command gates a pipeline directly. Each result lists pass or fail per
operation with the exchanged messages; the UI's *conformance index* rises
as you add examples per operation.

## Automating

- **Inside a test suite** → Testcontainers modules (Java, Node/TypeScript,
  Go, .NET) start a throwaway Microcks per run, serve mocks to consumer
  tests and run `testEndpoint(...)` conformance tests against the app.
  Open [references/testcontainers.md](references/testcontainers.md) when
  writing that test code; it has per-language APIs and the ensemble for
  Postman and async.
- **In CI** → `microcks import` then `microcks test`, or the
  `microcks/import-github-action` and `microcks/test-github-action` pair,
  with Keycloak service-account credentials from CI secrets. Open
  [references/automation.md](references/automation.md) when wiring CI,
  installing a shared instance, authenticating, or testing async APIs
  (broker URL formats, one operation per test).

## Practical notes

- **Import fails or the API shows zero operations** → the spec is invalid
  or lacks `info.title`/`info.version`; lint it first.
- **400 "dispatch criteria" from a mock** → no example matches the
  request: add one for that variant or set a `FALLBACK` dispatcher.
- **Several files for one API** → the spec with `mainArtifact=true`, each
  overlay or collection with `mainArtifact=false`, all with the same title
  and version or they land on separate APIs.
- **A spec you must not edit** (generated, another team's) → never fork a
  second copy for examples; layer `APIExamples`/`APIMetadata` overlays as
  secondary artifacts ([references/openapi-mocking.md](references/openapi-mocking.md)).
- **Mocks are stateless.** POST/PUT/DELETE return their examples but store
  nothing; use a `SCRIPT` dispatcher if a test needs state.
- **Secured implementations** → store credentials as a Microcks *Secret*
  and pass its `secretName` to the test, never a token in the command.
- **Keep specs in git and re-import on change** (CI import step or a
  scheduled importer) so mocks and tests never drift from the source.

## References

- [references/openapi-mocking.md](references/openapi-mocking.md) — named
  examples, request/response pairing, `x-microcks-refs`,
  `x-microcks-operation`, APIExamples/APIMetadata overlays, delays.
- [references/asyncapi-mocking.md](references/asyncapi-mocking.md) —
  AsyncAPI 2.x/3.x conventions, the async minion, per-protocol mock
  endpoints, event frequency, contract-testing producers.
- [references/dispatchers-and-templating.md](references/dispatchers-and-templating.md)
  — dispatcher catalog with rule syntax, and template functions for
  dynamic responses.
- [references/testcontainers.md](references/testcontainers.md) — mocks
  and contract tests from test code, per language, plus the ensemble.
- [references/automation.md](references/automation.md) — installs, the
  `microcks` CLI and exit codes, Keycloak auth, GitHub Actions, async test
  endpoint formats, choosing an approach.
