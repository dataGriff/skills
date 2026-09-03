# Contract testing with Microcks Testcontainers modules

Each module starts a throwaway Microcks (the single-container
`quay.io/microcks/microcks-uber` image — pin a version tag, e.g.
`:1.14.0`; `-native` variants boot faster) inside a test run. Same model
everywhere: load artifacts → consume mocks → `testEndpoint(...)` for the
conformance test. Modules are maintained by different contributors and can
drift; Java is the most feature-complete (webhooks, all async protocols).
Known gaps: Node and .NET lack webhook registration, Go lacks WebSocket
async, .NET lacks MQTT/SQS/SNS/PubSub, none support NATS.

## The pattern (any language)

1. Start `MicrocksContainer` with the spec as a main artifact (secondary
   artifacts add Postman collections / extra examples).
2. Consumer tests: point the client at
   `getRestMockEndpoint(name, version)` (or the soap/graphql/grpc
   equivalent). Optionally assert the mock was hit with
   `verify(name, version)` / `getServiceInvocationsCount(...)`.
3. Provider tests: start the app under test, then submit a test request —
   service id `"Name:version"`, runner type, `testEndpoint` reaching the
   app. When the app runs on the host, expose it and use
   `host.testcontainers.internal:<port>`.
4. Assert on the result's success flag; failure messages list the
   per-operation violations.

## Java — `io.github.microcks:microcks-testcontainers` (0.5.x)

```java
MicrocksContainer microcks = new MicrocksContainer(
        DockerImageName.parse("quay.io/microcks/microcks-uber:1.14.0"))
    .withMainArtifacts("apipastries-openapi.yaml");   // classpath or File
microcks.start();

String mockUrl = microcks.getRestMockEndpoint("API Pastries", "0.0.1");

TestRequest testRequest = new TestRequest.Builder()
    .serviceId("API Pastries:0.0.1")
    .runnerType(TestRunnerType.OPEN_API_SCHEMA.name())
    .testEndpoint("http://host.testcontainers.internal:" + port)
    .timeout(Duration.ofSeconds(2))
    .build();
TestResult result = microcks.testEndpoint(testRequest);
// Assertions helper: assertSuccess(result) or per operation/case:
// Assertions.assertSuccess(result, "GET /pastries/{name}", "Millefeuille");
```

Extras: `importAsMainArtifact(...)`/`importAsSecondaryArtifact(...)` after
start; `withSnapshots(...)` to load a full repository export;
`withSecret(new Secret.Builder()...)` for authenticated test endpoints
(then `.secretName(...)` on the request); `testEndpointAsync(...)` returns
a `CompletableFuture` so you can trigger app events mid-test;
`withWebhookRegistration(...)` for webhook callback tests.

## Node/TypeScript — `@microcks/microcks-testcontainers`

```ts
import { MicrocksContainer, TestRunnerType } from "@microcks/microcks-testcontainers";

const container = await new MicrocksContainer()
    .withMainArtifacts([path.resolve(resourcesDir, "api.yaml")])
    .start();

const mockUrl = container.getRestMockEndpoint("API Pastries", "0.0.1");

const testResult = await container.testEndpoint({
  serviceId: "API Pastries:0.0.1",
  runnerType: TestRunnerType.OPEN_API_SCHEMA,
  testEndpoint: "http://my-app:3001",
  timeout: 2000,
});
expect(testResult.success).toBe(true);
```

## Go — `microcks.io/testcontainers-go`

```go
import (
    microcks "microcks.io/testcontainers-go"
    client "microcks.io/go-client"
)

mc, err := microcks.Run(ctx, "quay.io/microcks/microcks-uber:1.14.0",
    microcks.WithMainArtifact("testdata/apipastries-openapi.yaml"))

mockUrl, _ := mc.RestMockEndpoint(ctx, "API Pastries", "0.0.1")

testResult, err := mc.TestEndpoint(ctx, &client.TestRequest{
    ServiceId:    "API Pastries:0.0.1",
    RunnerType:   client.TestRunnerTypeOPENAPISCHEMA,
    TestEndpoint: "http://implementation:3001",
    Timeout:      2000,
})
```

## .NET — `Microcks.Testcontainers` (NuGet)

Same shape: `new MicrocksBuilder().WithMainArtifacts(...).Build()`, then
`StartAsync()`, `GetRestMockEndpoint(...)`, `TestEndpointAsync(new
TestRequest {...})`.

## Ensemble: Postman runner and async APIs

The single container covers `HTTP`, `OPEN_API_SCHEMA`, `GRAPHQL_SCHEMA`,
`GRPC_PROTOBUF` and `SOAP` runners. The `POSTMAN` runner and AsyncAPI
mocking/testing need sidecar containers — use the ensemble on a shared
container network:

```ts
const network = await new Network().start();
const ensemble = await new MicrocksContainersEnsemble(network)
    .withMainArtifacts([...])
    .withPostman()                                     // POSTMAN runner
    .withAsyncFeature()                                // async-minion
    .withKafkaConnection({ bootstrapServers: "kafka:9092" })
    .start();
const microcks = ensemble.getMicrocksContainer();
```

(Java: `new MicrocksContainersEnsemble(image).withPostman()
.withAsyncFeature().withKafkaConnection(new KafkaConnection("kafka:9092"))`;
Go: `ensemble.RunContainers(ctx, ensemble.WithPostman(true), ...)`.)

For async mocks, topic/destination names come from the async-minion, e.g.
Java `ensemble.getAsyncMinionContainer().getKafkaMockTopic(name, version,
"SUBSCRIBE topic/path")`. Async conformance tests use runner
`ASYNC_API_SCHEMA` with a broker URL as `testEndpoint` — URL formats are in
[automation.md](automation.md).
