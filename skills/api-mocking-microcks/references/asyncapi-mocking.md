# AsyncAPI mocking conventions

How Microcks mocks event-driven APIs from AsyncAPI 2.x and 3.x documents,
and how to enable the async infrastructure. Mocking here means: Microcks
**publishes the spec's example messages on a real broker/channel at a fixed
frequency**, so consumers under development have live traffic to subscribe
to. It can also contract-test a producer by listening to its output.

## Enabling async support

Async mocking is not on by default — it needs the **async minion**
component, which connects to brokers and does the publishing.

**Local, no broker (WebSocket only):** the plain
`quay.io/microcks/microcks-uber` image mocks WebSocket channels with
nothing extra — the WebSocket server is built into Microcks itself.

**Local with Kafka and other protocols:** run the uber async minion next to
the uber image and give it a broker:

```bash
docker network create microcks
docker run -d --name kafka --network microcks -p 9092:9092 <kafka image>
docker run -d --name microcks --network microcks -p 8585:8080 \
  quay.io/microcks/microcks-uber:1.14.0
docker run -d --name microcks-async-minion --network microcks -p 8081:8081 \
  -e MICROCKS_HOST_PORT=microcks:8080 \
  -e ASYNC_PROTOCOLS=KAFKA \
  -e KAFKA_BOOTSTRAP_SERVER=kafka:9092 \
  quay.io/microcks/microcks-uber-async-minion:1.14.0
```

**Docker-compose / Kubernetes:** the microcks repo ships an async addon
compose file (`docker-compose.yml` + `docker-compose-async-addon.yml`,
which brings its own Kafka), and the Helm chart/operator take
`features.async.enabled=true`. See automation-and-testing.md for the base
installs. Testcontainers modules expose the same thing as a
`MicrocksContainersEnsemble` with async enabled.

Supported protocols: Kafka, WebSocket, MQTT, AMQP (RabbitMQ), NATS, Google
Pub/Sub, Amazon SQS/SNS. Set the ones you need in `ASYNC_PROTOCOLS` and
provide connection env vars for each broker.

## Message examples (AsyncAPI 2.x)

Identity is `info.title` + `info.version`, as for OpenAPI. Examples live on
the message, as a list of named `{headers, payload}` objects:

```yaml
asyncapi: "2.6.0"
info:
  title: User signed-up API
  version: "0.1.0"
channels:
  user/signedup:
    subscribe:                 # events the API emits → Microcks publishes these
      message:
        $ref: "#/components/messages/UserSignedUp"
components:
  messages:
    UserSignedUp:
      payload:
        type: object
        properties:
          id: { type: string }
          email: { type: string }
      examples:
        - name: john
          payload: { id: "{{ guid() }}", email: john@example.com }
        - name: jane
          payload: { id: "{{ guid() }}", email: jane@example.com }
```

Payloads may use the same `{{ }}` template functions as REST mocks
(dispatchers-and-templating.md), so every published event can carry fresh
ids/timestamps. Examples must conform to the payload schema — Microcks
validates them for contract tests.

**AsyncAPI 3.x** is supported too (Microcks ≥ 1.8): channels and operations
are split, and examples sit on the message object referenced from the
channel; operations with the emitting direction (the app *sends*) are the
ones Microcks publishes mocks for. Prefer 2.6 conventions when you control
the file format choice — tooling is broadest there.

## Where the events land

For each mocked operation Microcks derives a destination (the API detail
page in the UI shows the exact one per protocol — copy from there):

- **Kafka**: topic named from the API name, version, and channel with
  non-alphanumerics sanitized to dashes, e.g.
  `UsersignedupAPI-0.1.0-user-signedup`.
- **WebSocket**: `ws://<microcks>/api/ws/<API name>/<version>/<channel>` —
  connect and messages arrive at the mock frequency.
- **MQTT/AMQP/NATS/…**: channel-derived topic/queue on the configured
  broker.

Default publication frequency is every 3 seconds; override per operation:

```yaml
    subscribe:
      x-microcks-operation:
        frequency: 30          # seconds between publications
```

Quick verification for Kafka:
`kcat -b localhost:9092 -t 'UsersignedupAPI-0.1.0-user-signedup' -C` and
watch john/jane alternate.

## Contract-testing producers

The `ASYNC_API_SCHEMA` test runner inverts the flow: Microcks *listens* on
the real application's topic/endpoint for a while and validates every
captured message against the AsyncAPI payload schema.

```bash
microcks-cli test 'User signed-up API:0.1.0' \
  kafka://mybroker:9092/app.signups ASYNC_API_SCHEMA \
  --microcksURL=http://localhost:8585/api/ \
  --keycloakClientId=foo --keycloakClientSecret=bar \
  --waitFor=20sec
```

The test endpoint is a protocol URL (`kafka://…`, `ws://…`, `mqtt://…`)
pointing at the *system under test's* broker and topic, not at Microcks.
Common failure: `waitFor` shorter than the app's publish interval — nothing
is captured and the test errors rather than fails.

## Gotchas

- No traffic on the topic? Check the async minion's logs first — it is a
  separate container/pod and silently does nothing when it can't reach the
  broker or Microcks (`MICROCKS_HOST_PORT`).
- Only channels with the emitting direction are mocked; a 2.x `publish`
  operation (events the app consumes) produces no mock traffic.
- Each example message must include values for any channel parameters, or
  the destination cannot be resolved.
- WebSocket mocks work on the plain uber image, so prefer WebSocket for
  broker-free demos and CI smoke tests.
