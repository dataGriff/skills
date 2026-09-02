# Protocol bindings

Bindings attach protocol-specific configuration without polluting the
portable core of the document. They exist at four levels, and each is a map
of protocol name → binding object:

| Level     | Field                | Typical content                                  |
| --------- | -------------------- | ------------------------------------------------ |
| server    | `servers.*.bindings`   | broker-wide config (schema registry URL)       |
| channel   | `channels.*.bindings`  | topic/queue definition (partitions, durability)|
| operation | `operations.*.bindings`| consumer/producer config (groupId, qos, ack)   |
| message   | `channels.*.messages.*.bindings` | wire framing (key, schema id location)|

Rules of thumb:

- Only add a binding when the protocol detail is part of the contract —
  consumers need it, or infra is provisioned from it. Empty binding
  objects (`kafka: {}`) are legitimate as "this exists on Kafka" markers
  but usually noise.
- **Pin `bindingVersion`** in every binding object. It defaults to
  `latest`, which changes meaning as the bindings repo evolves.
- Binding definitions live in a separate repo per protocol:
  https://github.com/asyncapi/bindings — consult it for any protocol or
  field not listed here. Supported protocol keys include `kafka`, `amqp`,
  `amqp1`, `mqtt`, `mqtt5`, `ws`, `http`, `nats`, `jms`, `sns`, `sqs`,
  `anypointmq`, `googlepubsub`, `pulsar`, `ibmmq`, `solace`, `stomp`,
  `mercure`, `ros2`.
- Reusable binding maps go under `components/serverBindings`,
  `channelBindings`, `operationBindings`, `messageBindings`.

## Kafka (bindingVersion 0.5.0)

**Server binding** — schema registry wiring:

```yaml
servers:
  production:
    host: kafka.example.com:9092
    protocol: kafka
    bindings:
      kafka:
        schemaRegistryUrl: 'https://registry.example.com'
        schemaRegistryVendor: confluent   # apicurio | confluent | ibm | karapace
        bindingVersion: 0.5.0
```

**Channel binding** — topic definition (`topic` only when the Kafka topic
name differs from the channel `address`):

```yaml
channels:
  orderPlaced:
    address: orders.placed
    bindings:
      kafka:
        partitions: 12
        replicas: 3
        topicConfiguration:
          retention.ms: 604800000
          cleanup.policy: [delete]
        bindingVersion: 0.5.0
```

**Operation binding** — `groupId` and `clientId` are *Schema Objects*
(usually `type: string` with an `enum` naming the actual group), not bare
strings:

```yaml
operations:
  receiveOrderPlaced:
    action: receive
    channel: {$ref: '#/channels/orderPlaced'}
    bindings:
      kafka:
        groupId:
          type: string
          enum: [billing-service]
        bindingVersion: 0.5.0
```

**Message binding** — partition `key` (also a Schema Object), plus schema
registry framing: `schemaIdLocation` (`header` or `payload`),
`schemaIdPayloadEncoding` (e.g. `confluent`, or a byte count),
`schemaLookupStrategy`:

```yaml
messages:
  orderPlaced:
    bindings:
      kafka:
        key:
          type: string
          description: The order id — keeps one order's events in sequence.
        schemaIdLocation: payload
        schemaIdPayloadEncoding: confluent
        bindingVersion: 0.5.0
```

## Other common protocols, in brief

Verify exact fields against https://github.com/asyncapi/bindings/tree/master/<protocol>
before writing them — versions and fields evolve independently per protocol.

- **AMQP 0-9-1 (`amqp`)** — channel binding declares `is: queue` or
  `is: routingKey` with a nested `queue` (`name`, `durable`, `exclusive`,
  `autoDelete`, `vhost`) or `exchange` (`name`, `type: topic|direct|fanout|
  default|headers`, `durable`, `autoDelete`, `vhost`); operation binding
  carries `ack`, `deliveryMode`, `cc`/`bcc`, `expiration`, `mandatory`;
  message binding carries `contentEncoding`, `messageType`.
- **MQTT (`mqtt`)** — server binding: `clientId`, `cleanSession`,
  `lastWill` (`topic`, `qos`, `message`, `retain`), `keepAlive`; operation
  binding: `qos` (0/1/2), `retain`; MQTT 5 additions live in the same
  binding (e.g. `sessionExpiryInterval`).
- **WebSockets (`ws`)** — channel binding only: `method` (`GET`/`POST`),
  `query` and `headers` as Schema Objects describing the handshake request.
  Remember: query strings never go in the channel `address`.
- **HTTP (`http`)** — operation binding: `method`, `query`; message
  binding: `headers`, `statusCode`. Used for webhooks and
  server-sent-event style APIs described in AsyncAPI.

## Choosing the level

Put a fact at the level where it is true for everything below it: a schema
registry serves the whole broker (server); partitions belong to the topic
(channel); a consumer group belongs to this application's act of consuming
(operation); the record key is a property of each message (message). If a
binding fact differs per environment, it probably isn't contract — leave it
to deployment config.
