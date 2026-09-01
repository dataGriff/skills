# Automation: installs, CLI, Testcontainers, contract tests

## Installation options

| Option | Use for | Notes |
| --- | --- | --- |
| `microcks-uber` container | local dev, CI jobs | single container, no auth; `-native` tag variant starts in ~ms |
| Testcontainers module | inside test suites | throwaway instance per test run |
| docker/podman-compose | shared dev instance | full stack: Keycloak auth, MongoDB, optional Kafka |
| Helm chart / operator | team/production instance | `features.async.enabled=true` for events; scheduled importers |

Full compose stack (from the microcks repo):

```bash
git clone https://github.com/microcks/microcks.git --depth 1
cd microcks/install/docker-compose
docker compose up -d                                   # core stack
docker compose -f docker-compose.yml -f docker-compose-async-addon.yml up -d  # + Kafka & async minion
```

Compose stack default login is `admin`; the generated password is in the
Keycloak realm config — check the install README rather than guessing.

## microcks-cli

Small Go binary (also `quay.io/microcks/microcks-cli` image) with two
commands, made for CI. Against an unauthenticated (uber) instance the
Keycloak flags are still required — pass dummy values:

```bash
# Import: comma-separated <path>:<isMainArtifact> pairs
microcks-cli import 'specs/order-api.yaml:true,specs/order-examples.yaml:false' \
  --microcksURL=http://localhost:8585/api/ \
  --keycloakClientId=foo --keycloakClientSecret=bar

# Contract test: validate a real implementation against the spec
microcks-cli test 'Order API:1.0' http://app.staging.svc:8080/api OPEN_API_SCHEMA \
  --microcksURL=http://localhost:8585/api/ \
  --keycloakClientId=microcks-serviceaccount --keycloakClientSecret=<secret> \
  --waitFor=10sec --insecure
```

Test runners: `HTTP` (reachability only), `OPEN_API_SCHEMA`,
`ASYNC_API_SCHEMA`, `POSTMAN` (runs collection test scripts, so business
assertions), `SOAP_UI`, `SOAP` (semantic SOAP validation), `GRPC_PROTOBUF`,
`GRAPHQL_SCHEMA`. Schema runners replay every example request against the
endpoint and validate responses against the spec schemas; exit code is
non-zero on failure, so the command gates pipelines directly. Useful extras:
`--secretName` (broker/endpoint credentials stored in Microcks),
`--filteredOperations`, `--operationsHeaders`.

GitHub Actions wrappers exist: `microcks/import-github-action` and
`microcks/test-github-action` (same parameters as the CLI). On a long-lived
instance, prefer configuring a **scheduled importer** (Importers page or
`import-github-action` on merge) pointing at the spec's raw git URL — mocks
then track the repo automatically.

## Testcontainers

Modules for Java, Node/TS, Go, Python, .NET wrap the uber image. Node:

```typescript
import { MicrocksContainer } from "@microcks/microcks-testcontainers";

const microcks = await new MicrocksContainer("quay.io/microcks/microcks-uber:1.14.0")
  .withMainArtifacts(["specs/order-api.yaml"])
  .withSecondaryArtifacts(["specs/order-examples.yaml"])
  .start();

const baseUrl = microcks.getRestMockEndpoint("Order API", "1.0");
// point the code under test at baseUrl, e.g. GET `${baseUrl}/orders/123`
```

Java is the same shape (`MicrocksContainer` from
`io.github.microcks:microcks-testcontainers`); Go uses
`microcks.Run(ctx, image, microcks.WithMainArtifact("..."))`
(`microcks.io/testcontainers-go`); Python (`microcks-testcontainers` on
PyPI) uses snake_case:

```python
from microcks_testcontainers import MicrocksContainer

with MicrocksContainer() as microcks:
    microcks.upload_main_artifact("specs/order-api.yaml")
    base_url = microcks.get_rest_mock_endpoint("Order API", "1.0")
```

All modules can also *run contract tests* from inside the suite — start the
app under test (often another container on the same network), then:

```typescript
const result = await microcks.testEndpoint({
  serviceId: "Order API:1.0",
  runnerType: TestRunnerType.OPEN_API_SCHEMA,
  testEndpoint: "http://app:8080/api",
  timeout: 5000,
});
expect(result.success).toBe(true);
```

For async APIs use the ensemble variant
(`MicrocksContainersEnsemble` with async features enabled) which starts the
async minion alongside; it exposes per-protocol mock endpoints such as
`getAsyncMinionContainer().getWSMockEndpoint(...)` / Kafka topic helpers.

Verification helpers worth knowing: `microcks.getMessagesForTestCase(...)`
inspects what a contract test exchanged, and invocation-count APIs let a
test assert the mock was actually called.

## Choosing an approach

- **Unit/integration tests** → Testcontainers; specs imported per run, no
  shared state, endpoint injected into the app under test.
- **Ephemeral CI mock for e2e jobs** → run the uber image as a service
  container, import with `microcks-cli` (dummy Keycloak flags), curl mocks.
- **Shared team sandbox** → compose/Helm install + scheduled importers from
  git; humans browse the catalog, apps point at stable mock URLs.
- **Deployment gate** → `microcks-cli test` (or the GitHub Action) against
  the freshly deployed environment with `OPEN_API_SCHEMA` /
  `ASYNC_API_SCHEMA` runners.
