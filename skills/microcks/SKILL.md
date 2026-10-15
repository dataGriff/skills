---
name: microcks
description: >-
  Mock and contract-test APIs from their specs with Microcks: spec
  examples that become live mocks, dispatcher rules, event mocks, and
  conformance tests of a running implementation from Testcontainers, the
  microcks CLI or GitHub Actions. Use when the user mentions Microcks,
  wants to mock an API, backend or broker from an OpenAPI or AsyncAPI
  spec, needs fake endpoints or sample events, or wants contract,
  conformance or provider testing. Writing the spec itself is
  openapi-authoring or asyncapi-authoring.
---

# Microcks

Microcks serves a spec's **named examples** as mocks and replays the same
examples against a real implementation to test conformance. It never
invents data: an operation without examples has no mock and no test. An
API's identity is `info.title` + `info.version`, referenced everywhere as
`Name:version`. The spec is the *main* artifact; overlays and Postman
collections are *secondary* artifacts layered onto it.

Most of this you can do from general knowledge. This skill carries the
facts that fail silently, at import or at runtime, when guessed.

## Facts that fail silently

**Mocks**
- Pair an exchange by example name: the same name on the request
  parameters or body and on the response example that answers it, with
  every required parameter valued. Unpaired examples mock nothing.
- `JSON_BODY` dispatcher rules need all three fields, and case keys are
  bare values or intervals; case values must be existing response example
  names, or every call returns 400:

  ```json
  {"exp": "/amount", "operator": "range",
   "cases": {"[1;10000]": "approved", "[10001;50000]": "pending", "default": "rejected"}}
  ```

  Not `"range[1;10]"`, not `"range(1,10)"`; `]a;b[` is exclusive.
- A spec you must not edit (generated, another team's) gets
  `APIExamples` / `APIMetadata` overlays (`apiVersion:
  mocks.microcks.io/v1alpha1`) imported as secondary artifacts. Their
  `metadata.name` and `metadata.version` must equal the spec's
  `info.title` and `info.version` exactly, or they create a separate API.
  Never fork a second copy of the spec.
- Mocks are stateless: writes return their example and store nothing.

**Contract tests**
- Runner ids are an exact enum: `OPEN_API_SCHEMA`, `ASYNC_API_SCHEMA`,
  `GRPC_PROTOBUF`, `GRAPHQL_SCHEMA`, `POSTMAN`, `SOAP_UI`, `SOAP`, `HTTP`.
  `OPENAPI_SCHEMA` and similar near misses fail only at runtime.
- `testEndpoint` is the implementation's base URL, not Microcks'.
- Async tests (`ASYNC_API_SCHEMA`) point at the implementation's broker
  (`kafka://host:9092/topic`, `ws://…`, `mqtt://…`) and test one operation
  at a time; a `waitFor` shorter than the publish interval captures
  nothing.

**Tooling**
- The 1.x CLI binary is `microcks` (`brew install microcks/tap/microcks`
  or the `quay.io/microcks/microcks-cli` image); `microcks-cli` is the
  pre-1.0 name. `microcks import 'spec.yaml:true,overlay.yaml:false'`,
  then `microcks test 'Name:version' <endpoint> <RUNNER> --microcksURL=…/api/`.
  Exit code 1 is a contract violation; 11 and up are infrastructure.
- `--keycloakClientId` and `--keycloakClientSecret` go together, from CI
  secrets, and only against a Keycloak-secured instance. TLS skip is
  `--insecure-tls`.
- `microcks test --dry-run --artifact ./spec.yaml …` tests with no server.
- `microcks/import-github-action@v1` (`specificationFiles`) and
  `microcks/test-github-action@v1` (`apiNameAndVersion`, `testEndpoint`,
  `runner`, `microcksURL`, `waitFor`) wrap the 0.5.x CLI, so `--dry-run`
  and `--output` need the CLI image run directly.
- Testcontainers modules exist for Java, Node/TypeScript
  (`@microcks/microcks-testcontainers`), Go and .NET; there is no Python
  module. Take mock URLs from `getRestMockEndpoint(name, version)`, never
  a hand-built URL or port.
- Local server: `quay.io/microcks/microcks-uber:<pinned tag>`, no auth.
  Compose stacks in the microcks repo: `docker-compose-devmode.yml`, or
  `docker-compose.yml` plus `async-addon.yml` for events.

## References

The facts above cover writing mockable specs, `JSON_BODY` dispatch,
overlays, GitHub Actions import and test steps, and Node Testcontainers
tests. When they answer the task, write the result without opening a
reference: each read costs a whole turn. Open one only for what they leave
out:

- [references/openapi-mocking.md](references/openapi-mocking.md) — only
  for `x-microcks-refs`, `x-microcks-operation` fields, or overlay fields
  beyond examples, labels and delays.
- [references/asyncapi-mocking.md](references/asyncapi-mocking.md) — only
  when configuring the async minion or a broker other than WebSocket.
- [references/dispatchers-and-templating.md](references/dispatchers-and-templating.md)
  — only for SCRIPT, FALLBACK or PROXY dispatchers, or template functions
  other than `{{ guid() }}`, `{{ now() }}`, `{{ randomInt() }}` and
  `{{ request.body/<pointer> }}`.
- [references/testcontainers.md](references/testcontainers.md) — only for
  Java, Go or .NET test code, or the ensemble (Postman runner, async).
- [references/automation.md](references/automation.md) — only when
  installing Microcks itself (compose, Helm), using CLI flags not named
  above, or wiring CI other than GitHub Actions.
