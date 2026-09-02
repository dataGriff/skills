# Automating Microcks contract tests (CLI, CI, async endpoints)

## The `microcks` CLI (1.x)

Install: binaries from github.com/microcks/microcks-cli releases,
`brew install microcks/tap/microcks`, or container image
`quay.io/microcks/microcks-cli`. (Older 0.5.x docs call the binary
`microcks-cli` with the same `test` verb — prefer the 1.x `microcks`
binary.)

### `microcks test`

```bash
microcks test '<serviceName:version>' <testEndpoint> <runner> \
  --microcksURL=https://microcks.example.com/api \
  --keycloakClientId=microcks-serviceaccount \
  --keycloakClientSecret=$MICROCKS_SA_SECRET \
  --waitFor=10sec
```

Runners: `HTTP`, `SOAP`, `SOAP_UI`, `POSTMAN`, `OPEN_API_SCHEMA`,
`ASYNC_API_SCHEMA`, `GRPC_PROTOBUF`, `GRAPHQL_SCHEMA`.

Useful flags:

- `--output` — `text` (default), `json`, `yaml`, or `github-actions`
  (annotations + step summary; `MICROCKS_ACTIONS_VERBOSE=true` also
  annotates passing operations).
- `--dry-run --artifact ./spec.yaml` — spins up an ephemeral Microcks
  container locally, imports the artifact, tests, tears down: contract
  tests with no server and no auth. `--watch` re-runs on artifact change;
  `--ready-timeout` (default 90s) bounds container startup.
- `--waitFor` — how long Microcks waits for the test to complete.
- `--secretName` — Microcks Secret used to reach a protected testEndpoint.
- `--filteredOperations='["GET /pastries"]'` — test a subset of operations.
- `--operationsHeaders='{"globals":[{"name":"x-api-key","values":"…"}]}'` —
  extra headers, globally or per operation.
- TLS/config: `--insecure-tls`, `--caCerts`, `--verbose`,
  `--config`/`--microcks-context` (contexts managed via `microcks login` /
  `microcks context`).

Exit codes: `0` contract holds, `1` contract violated, `2` usage error,
`11–14` connectivity/precondition errors, `20` other — gate pipelines on
non-zero, but distinguish 1 (real failure) from 11+ (infrastructure).

### Importing from pipelines

```bash
microcks import 'openapi.yaml'                 # main artifact
microcks import 'postman-collection.json:false'  # :false = secondary
microcks import-url 'https://…/openapi.yaml'
microcks import-dir ./specs
```

Import before test in the same pipeline so the tested contract is the
committed one. For continuous sync outside CI, prefer a Microcks importer
job polling the git raw URL.

## Authentication (shared instances)

CI talks to Microcks through a Keycloak *service account*: a confidential
client (default `microcks-serviceaccount`) in the Microcks realm. Pass its
id/secret via `--keycloakClientId`/`--keycloakClientSecret` (or the
matching action inputs), stored as CI secrets. Instances installed without
Keycloak (devmode/uber) accept any value there.

## GitHub Actions

```yaml
- uses: microcks/test-github-action@v1
  with:
    apiNameAndVersion: 'API Pastry - 2.0:2.0.0'
    testEndpoint: 'https://my-api.staging.example.com'
    runner: OPEN_API_SCHEMA
    microcksURL: 'https://microcks.example.com/api/'
    keycloakClientId: ${{ secrets.MICROCKS_SERVICE_ACCOUNT }}
    keycloakClientSecret: ${{ secrets.MICROCKS_SERVICE_ACCOUNT_CREDENTIALS }}
    waitFor: '10sec'
```

Optional inputs mirror the CLI: `secretName`, `filteredOperations`,
`operationsHeaders`. There is a matching `microcks/import-github-action`.
Alternatively run the CLI container directly with
`--output=github-actions`. Equivalent integrations exist for Jenkins
(plugin), GitLab CI and Tekton (CLI image), documented at microcks.io under
Guides → Automating.

## Test endpoint URL formats

HTTP-based (REST, SOAP, GraphQL, gRPC):
`http[s]://host[:port][/base-path]` — Microcks appends operation paths.

Event-based (`ASYNC_API_SCHEMA`) — point at the broker the implementation
publishes to; test **one operation at a time** (`filteredOperations` with a
single entry when the API has several):

| Protocol      | Format                                                  |
| ------------- | ------------------------------------------------------- |
| Kafka         | `kafka://broker:port/topic` (opt. `?registryUrl=…`)     |
| MQTT          | `mqtt://broker:port/topic`                              |
| AMQP          | `amqp://broker:port/[vhost/]{type}/{name}`              |
| WebSocket     | `ws://endpoint:port/channel`                            |
| NATS          | `nats://endpoint:port/subject`                          |
| Google PubSub | `googlepubsub://project/topic`                          |
| SQS / SNS     | `sqs://region/queue` / `sns://region/topic`             |

Broker credentials/certs go in a Microcks Secret referenced by the test's
`secretName`.
