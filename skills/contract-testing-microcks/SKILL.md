---
name: contract-testing-microcks
description: >-
  Run API contract testing with Microcks (microcks.io): turn OpenAPI,
  AsyncAPI, gRPC/Protobuf, GraphQL, Postman or SoapUI artifacts into live
  mocks, then verify a running implementation conforms to its contract using
  Microcks test runners — locally via Testcontainers or docker compose, and
  in CI via the microcks CLI or GitHub Action. Use when the user mentions
  Microcks, contract testing, conformance testing, provider contract tests,
  validating an API implementation against its spec, mocking an API from its
  spec for consumer tests, or wiring contract checks into a pipeline. Pairs
  with openapi-authoring / asyncapi-authoring for writing the spec itself.
---

# Contract testing with Microcks

Microcks is the CNCF tool for mocking and contract-testing APIs directly
from their specs — REST (OpenAPI), event-driven (AsyncAPI), gRPC, GraphQL
and SOAP. As of 2026 the current release line is 1.14+. The contract is the
spec **plus its examples**: Microcks imports the artifact, serves the
examples as live mocks (consumer side), and replays them against a running
implementation to check conformance (provider side).

## Pick a deployment

- **Inside automated tests (preferred for dev loops):** Testcontainers
  modules for Java, Node/TypeScript, Go and .NET spin up a throwaway
  Microcks per test run — no shared instance, no auth. Open
  [references/testcontainers.md](references/testcontainers.md) when writing
  test code with these modules.
- **Local instance:**

  ```bash
  git clone https://github.com/microcks/microcks.git --depth 10
  cd microcks/install/docker-compose
  docker compose -f docker-compose-devmode.yml up -d
  ```

  Devmode skips Keycloak and bundles async support (Red Panda broker); UI
  at http://localhost:8080. The full `docker-compose.yml` adds Keycloak —
  its default admin / microcks123 login is for local development only;
  stack async support on it with `-f async-addon.yml`.
- **Shared/team instance:** Helm chart or operator on Kubernetes; CI then
  targets that instance with a Keycloak service account.

## Core loop

1. **Import artifacts.** Upload specs via UI, importer jobs (git URL), CLI
   (`microcks import`), or Testcontainers `withMainArtifacts(...)`. One
   *main* artifact defines the service (e.g. the OpenAPI file); *secondary*
   artifacts layer extra examples or test scripts onto it (e.g. a Postman
   collection, an APIMetadata file). Mocks only exist for operations that
   have examples — a spec without examples imports but mocks nothing, so
   enrich the spec's `examples` first.
2. **Point consumers at the mocks.** REST mocks live under
   `/rest/{service}/{version}/...` on the Microcks endpoint; equivalent
   prefixes exist for SOAP, GraphQL, gRPC, and async brokers.
3. **Run a conformance test** against the real implementation: give
   Microcks the service (`"Name:version"`), the implementation's
   `testEndpoint`, and a runner:

   | Runner            | For             | Validates                          |
   | ----------------- | --------------- | ---------------------------------- |
   | `HTTP`            | REST, SOAP      | endpoint answers 2xx/404 sensibly  |
   | `OPEN_API_SCHEMA` | REST            | status + response schema vs OpenAPI|
   | `ASYNC_API_SCHEMA`| events          | messages vs AsyncAPI schema        |
   | `GRPC_PROTOBUF`   | gRPC            | responses vs Protobuf schema       |
   | `GRAPHQL_SCHEMA`  | GraphQL         | responses vs GraphQL schema        |
   | `POSTMAN`         | REST/SOAP/GQL   | Postman collection test scripts    |
   | `SOAP` / `SOAP_UI`| SOAP            | XSD schemas / SoapUI assertions    |

   Default to the `*_SCHEMA` runner for the API's protocol; use `POSTMAN`
   when business assertions (beyond schema shape) are required — that needs
   the collection imported as a secondary artifact.
4. **Read the result.** Each test reports pass/fail per operation with
   exchanged messages. The UI also tracks a *conformance index* (how well
   samples cover the contract) and *conformance score* (test outcomes) —
   improve the index by adding examples per operation.

## Quick test from a shell

```bash
# against a running Microcks (CLI 1.x binary is `microcks`)
microcks test 'Pastry API:1.0.0' http://localhost:3000 OPEN_API_SCHEMA \
  --microcksURL=http://localhost:8585/api --waitFor=10sec

# no server at all: ephemeral container from a local spec
microcks test --dry-run --artifact ./openapi.yaml \
  'Pastry API:1.0.0' http://localhost:3000 OPEN_API_SCHEMA
```

Exit code 0 means the contract holds; 1 means violations (safe to gate
pipelines on). Open [references/automation.md](references/automation.md)
when wiring CI (GitHub Action, CLI flags/auth, exit codes) or when testing
async APIs (broker `testEndpoint` URL formats, one-operation-per-test rule).

## Practical notes

- Naming: the service name/version come from the artifact (OpenAPI
  `info.title` + `info.version`), and tests reference `"Name:version"`
  exactly — mismatches are the most common "service not found" cause.
- `testEndpoint` is the base URL of the *implementation under test*, not
  Microcks; Microcks appends each operation's path to it.
- Keep specs and examples in git and re-import on change (importer job or
  CI import step) so mocks and tests never drift from the source of truth.
- A failing conformance test means fix the implementation, or renegotiate
  the spec with its consumers and bump its version — never trim examples
  or loosen schemas just to pass: the spec is the agreement being gated.
- Secured implementations: store credentials as a Microcks *Secret* and
  pass its `secretName` to the test rather than embedding tokens.

## References

- [references/testcontainers.md](references/testcontainers.md) — writing
  contract tests with the Testcontainers modules: per-language setup (Java,
  Node, Go, .NET), mock endpoints, ensemble for Postman/async, verify APIs.
- [references/automation.md](references/automation.md) — CLI command/flag
  reference and exit codes, Keycloak service-account auth, GitHub Action,
  other CI integrations, async test endpoint URL formats.
