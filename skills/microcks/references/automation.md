# Automating Microcks: installs, CLI, CI, async test endpoints

## Contents

- Installation options
- The `microcks` CLI (import, test, exit codes)
- Authentication on shared instances
- GitHub Actions and other CI
- Test endpoint URL formats
- Choosing an approach

## Installation options

| Option | Use for | Notes |
| --- | --- | --- |
| `microcks-uber` container | local dev, CI jobs | single container, no auth; `-native` tag variant boots fastest |
| `microcks start` / `microcks stop` | local dev from the CLI | runs the uber image via Docker/Podman |
| Testcontainers module | inside test suites | throwaway instance per run; [testcontainers.md](testcontainers.md) |
| docker/podman compose | shared dev instance | full stack: Keycloak, MongoDB, optional async |
| Helm chart / operator | team or production instance | `features.async.enabled=true` for events; scheduled importers |

Compose stacks ship in the microcks repo:

```bash
git clone https://github.com/microcks/microcks.git --depth 1
cd microcks/install/docker-compose
docker compose -f docker-compose-devmode.yml up -d     # no Keycloak, async bundled
docker compose up -d                                   # full stack with Keycloak
docker compose -f docker-compose.yml -f async-addon.yml up -d   # + async minion
```

Devmode serves the UI on http://localhost:8080. The full stack's Keycloak
login (admin / microcks123 by default) is for local development only;
check the install README for the current values rather than guessing.
`kafdrop-addon.yml`, `rabbitmq-addon.yml` and `nats-addon.yml` add brokers.

## The `microcks` CLI (1.x)

Install: `brew install microcks/tap/microcks`, binaries from the
microcks-cli GitHub releases, or the `quay.io/microcks/microcks-cli`
image. Pre-1.0 docs call the binary `microcks-cli`; the verbs are the
same, prefer the 1.x `microcks` binary.

### Import

```bash
microcks import 'specs/order-api.yaml:true,specs/order-examples.yaml:false' \
  --microcksURL=http://localhost:8585/api/
microcks import-url 'https://raw.githubusercontent.com/acme/apis/main/order-api.yaml'
microcks import-dir ./specs
```

`:true` marks the main artifact, `:false` a secondary one (APIExamples
overlay, Postman collection, APIMetadata). Import before testing in the
same pipeline so the tested contract is the committed one.

### Test

```bash
microcks test 'Order API:1.0' https://orders.staging.example.com/api OPEN_API_SCHEMA \
  --microcksURL=https://microcks.example.com/api/ \
  --keycloakClientId=microcks-serviceaccount \
  --keycloakClientSecret=$MICROCKS_SA_SECRET \
  --waitFor=10sec

# no server at all: ephemeral container from a local spec
microcks test --dry-run --artifact ./openapi.yaml \
  'Order API:1.0' http://localhost:3000 OPEN_API_SCHEMA
```

Runners: `HTTP`, `SOAP`, `SOAP_UI`, `POSTMAN`, `OPEN_API_SCHEMA`,
`ASYNC_API_SCHEMA`, `GRPC_PROTOBUF`, `GRAPHQL_SCHEMA`.

Useful flags:

- `--output` — `text` (default), `json`, `yaml`, or `github-actions`
  (annotations and a step summary; `MICROCKS_ACTIONS_VERBOSE=true` also
  annotates passing operations).
- `--dry-run --artifact <spec>` — ephemeral Microcks container: import,
  test, tear down; no server, no auth. `--watch` re-runs on change;
  `--ready-timeout` (default 90s) bounds startup.
- `--waitFor` — how long Microcks waits for the test to complete.
- `--secretName` — a Microcks Secret holding credentials for a protected
  test endpoint or broker.
- `--filteredOperations='["GET /orders/{id}"]'` — test a subset.
- `--operationsHeaders='{"globals":[{"name":"x-api-key","values":"…"}]}'`
  — extra headers, globally or per operation.
- TLS and config: `--insecure-tls`, `--caCerts`, `--verbose`, `--config` /
  `--microcks-context` (contexts via `microcks login` / `microcks context`).

Exit codes: `0` contract holds, `1` contract violated, `2` usage error,
`11–14` connectivity or precondition errors, `20` other. Gate pipelines
on non-zero, but treat 1 (a real violation) differently from 11+
(infrastructure).

## Authentication on shared instances

CI reaches a Keycloak-secured Microcks through a *service account*: a
confidential client (default `microcks-serviceaccount`) in the Microcks
realm. Pass `--keycloakClientId` and `--keycloakClientSecret` together
(or the matching action inputs) from CI secrets. Against an
unauthenticated instance (uber, devmode) leave both off.

## GitHub Actions and other CI

```yaml
- uses: microcks/import-github-action@v1
  with:
    specificationFiles: 'order-api.openapi.yaml:true'
    microcksURL: 'https://microcks.example.com/api/'
    keycloakClientId: ${{ secrets.MICROCKS_SERVICE_ACCOUNT }}
    keycloakClientSecret: ${{ secrets.MICROCKS_SERVICE_ACCOUNT_CREDENTIALS }}
- uses: microcks/test-github-action@v1
  with:
    apiNameAndVersion: 'Order API:1.2.0'
    testEndpoint: 'https://orders.staging.example.com'
    runner: OPEN_API_SCHEMA
    microcksURL: 'https://microcks.example.com/api/'
    keycloakClientId: ${{ secrets.MICROCKS_SERVICE_ACCOUNT }}
    keycloakClientSecret: ${{ secrets.MICROCKS_SERVICE_ACCOUNT_CREDENTIALS }}
    waitFor: '10sec'
```

Optional inputs mirror the CLI: `secretName`, `filteredOperations`,
`operationsHeaders`. Both actions wrap the 0.5.x CLI image, so 1.x-only
features (`--dry-run`, `--output`, the 1.x exit codes) need the CLI image
run directly, e.g. with `--output=github-actions`. Jenkins (plugin), GitLab CI and Tekton (CLI
image) are covered at microcks.io under Guides → Automating.

On a long-lived instance, prefer a **scheduled importer** (Importers page)
pointing at the spec's raw git URL, so mocks track the repo without a
pipeline step.

## Test endpoint URL formats

HTTP-based (REST, SOAP, GraphQL, gRPC): `http[s]://host[:port][/base-path]`
— Microcks appends each operation's path.

Event-based (`ASYNC_API_SCHEMA`): point at the broker the implementation
publishes to, and test **one operation at a time** (`filteredOperations`
with a single entry when the API has several):

| Protocol      | Format                                                  |
| ------------- | ------------------------------------------------------- |
| Kafka         | `kafka://broker:port/topic` (opt. `?registryUrl=…`)     |
| MQTT          | `mqtt://broker:port/topic`                              |
| AMQP          | `amqp://broker:port/[vhost/]{type}/{name}`              |
| WebSocket     | `ws://endpoint:port/channel`                            |
| NATS          | `nats://endpoint:port/subject`                          |
| Google PubSub | `googlepubsub://project/topic`                          |
| SQS / SNS     | `sqs://region/queue` / `sns://region/topic`             |

Broker credentials and certificates go in a Microcks Secret referenced by
`secretName`.

## Choosing an approach

- **Unit and integration tests** → Testcontainers: specs imported per run,
  no shared state, endpoints injected into the code under test.
- **Ephemeral CI mock for e2e jobs** → the uber image as a service
  container, `microcks import`, then call the mocks.
- **Shared team sandbox** → compose or Helm install plus scheduled
  importers from git; people browse the catalog, apps use stable mock URLs.
- **Deployment gate** → `microcks test` (or `test-github-action`) against
  the freshly deployed environment with `OPEN_API_SCHEMA` or
  `ASYNC_API_SCHEMA`.
