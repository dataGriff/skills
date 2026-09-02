---
name: asyncapi-authoring
description: >-
  Author, edit, review, and upgrade AsyncAPI documents — the specification
  for describing event-driven / message-driven APIs (Kafka, AMQP/RabbitMQ,
  MQTT, WebSockets, HTTP, and more). Targets AsyncAPI 3.1.0: servers,
  channels, operations (send/receive), messages, payload schemas (JSON
  Schema, Avro, Protobuf via multi-format schemas), protocol bindings,
  request-reply, traits, correlation IDs, security schemes, validation with
  the AsyncAPI CLI, and org style rules with Spectral. Use when the user
  wants to describe or document an event-driven API, topic, queue, or
  message flow; mentions AsyncAPI, asyncapi.yaml, an event catalog, or
  publishing/subscribing to events; asks to migrate an AsyncAPI 2.x
  document to 3.x; or wants to review an AsyncAPI file for correctness or
  convention compliance — even if they just say "write an AsyncAPI spec for
  X" or "document our Kafka topics".
---

# Authoring AsyncAPI documents

One document describes one *application* — the thing that connects to
brokers and sends or receives messages — against **AsyncAPI 3.1.0** (the
latest release; 3.0 guidance applies unchanged), conventionally saved as
`asyncapi.yaml`. The skeleton below carries the syntax for everything a
useful document needs; work from it directly and open the references only
for the cases listed at the end. Validate with `asyncapi validate <file>`
when the AsyncAPI CLI is installed (`npm i -g @asyncapi/cli`).

## The skeleton

```yaml
asyncapi: 3.1.0           # spec version — always 3.1.0 for new documents
info:
  title: Order Service    # the application, not the broker
  version: 1.0.0          # the API's semver, not the spec version
  description: Emits order events; reacts to payment authorizations.
  contact: {name: Order Platform Team, email: orders-team@example.com}
defaultContentType: application/json

servers:
  production:
    host: kafka.example.com:9092
    protocol: kafka                    # amqp | mqtt | ws | http | ...
    description: Production cluster. SASL/SCRAM required.
    security:
      - $ref: '#/components/securitySchemes/saslScram'

channels:                 # WHERE messages flow — id is for tooling,
  orderPlaced:            #   address is the wire truth
    address: orders.placed.v1          # topic / routing key / path
    description: One event per order successfully placed.
    messages:             # EVERY message any app puts on this channel
      orderPlaced:
        $ref: '#/components/messages/orderPlaced'
    bindings:
      kafka: {partitions: 12, replicas: 3, bindingVersion: 0.5.0}
  paymentAuthorized:
    address: payments.authorized.v1
    messages:
      paymentAuthorized:
        $ref: '#/components/messages/paymentAuthorized'

operations:               # WHAT this application does on those channels
  sendOrderPlaced:
    action: send          # send = this app sends; receive = it receives
    channel: {$ref: '#/channels/orderPlaced'}      # root channels only
    summary: Publish an event when a customer places an order.
    messages:             # subset of the channel's messages, ref'd
      - $ref: '#/channels/orderPlaced/messages/orderPlaced'   # THROUGH it
  receivePaymentAuthorized:
    action: receive
    channel: {$ref: '#/channels/paymentAuthorized'}
    summary: Mark the order as paid when its payment clears.
    bindings:
      kafka:
        groupId: {type: string, enum: [order-service]}   # a Schema Object
        bindingVersion: 0.5.0

components:               # reusable definitions — inert until $ref'd
  messages:
    orderPlaced:
      name: OrderPlaced
      summary: A customer completed checkout and an order was created.
      correlationId:
        location: '$message.header#/correlationId'   # runtime expression
      headers:            # application headers only, never protocol ones
        type: object
        properties:
          correlationId: {type: string, format: uuid}
      payload:
        $ref: '#/components/schemas/orderPlacedPayload'
      bindings:
        kafka:
          key: {type: string, description: Order id — keeps ordering.}
          bindingVersion: 0.5.0
      examples:
        - name: minimal
          payload: {orderId: 9dbc3d5e-..., totalAmount: 12.5, currency: EUR}
    paymentAuthorized:
      name: PaymentAuthorized
      summary: A payment for an order was authorized.
      payload: {$ref: '#/components/schemas/paymentAuthorizedPayload'}
  schemas:                # default schema language: JSON Schema draft 7
    orderPlacedPayload:   #   superset (+ discriminator, deprecated)
      type: object
      additionalProperties: false
      required: [orderId, totalAmount, currency]
      properties:
        orderId: {type: string, format: uuid, description: Order id.}
        totalAmount: {type: number, minimum: 0}
        currency: {type: string, pattern: '^[A-Z]{3}$'}
    paymentAuthorizedPayload:
      type: object
      required: [orderId, paymentId]
      properties:
        orderId: {type: string, format: uuid}
        paymentId: {type: string, format: uuid}
  securitySchemes:
    saslScram:
      type: scramSha512   # the mechanism only — never credentials
      description: Credentials provisioned by the platform team.
```

Only `asyncapi` and `info` (title + version) are required, but a useful
document declares its servers, every channel it touches, and an operation
for each thing the application actually does.

## The v3 mental model

- **Channels say *where*, operations say *what*.** In v2 these were fused
  (`publish`/`subscribe` under the channel) and notoriously inverted; in
  v3 there is no ambiguity.
- **The document describes *this application's* behavior.** `action: send`
  means the described application sends; readers invert for themselves.
- **Channel keys are identifiers; addresses are the wire truth.** Never
  put the address in the key. `address: null` means unknown at design time
  (e.g. a dynamically created reply queue).
- **Root = implemented, components = available.** Root operations must
  `$ref` root channels (never `#/components/...`); a root channel's
  `servers` list must `$ref` root servers. Anything under `components` is
  inert until referenced.
- **Operation messages point through the channel**
  (`#/channels/<id>/messages/<id>`), never into components. Omitting the
  list means all of the channel's messages; `[]` means none.

## Rules that matter

- **Non-JSON-Schema payloads use a multi-format schema** — anywhere a
  schema is allowed, swap in `{schemaFormat, schema}`:

  ```yaml
  payload:
    schemaFormat: 'application/vnd.apache.avro;version=1.9.0'
    schema: {type: record, name: OrderPlaced, fields: [...]}
  ```

  Avro/JSON-based schemas inline as objects, Protobuf/XSD as strings; an
  optional Avro field is the union `['null', string]` with
  `default: null`; pair the format with a matching `contentType`
  (e.g. `avro/binary`).
- **Every message on a channel must match exactly one message object** —
  keep payloads distinguishable, or tooling can't tell them apart.
- **Bindings carry protocol truth; pin `bindingVersion`** (it defaults to
  the moving target `latest`). Put each fact at the level it is true for:
  registry wiring on the server, partitions on the channel, `groupId` on
  the operation, record `key` on the message.
- **`info.version` is the API's semver** — major for breaking (removed or
  renamed address/field, narrowed payload), minor for additive. The
  `asyncapi` field changes only when adopting a newer spec release.
- **No secrets, ever.** Security schemes describe the mechanism; a
  `user:pass@host` anywhere is a review-blocking defect.
- **No invented fields.** Org metadata goes in `x-` specification
  extensions; anything else fails validation.
- **The v2→v3 inversion trap** when upgrading: v2 `publish` meant "others
  may publish here" — this app *receives* (`action: receive`); v2
  `subscribe` meant this app *sends*. Mapping keywords naively inverts the
  API. Also: v2 server `url` split into `host`/`protocol`/`pathname`;
  parameters lost `schema` (plain strings now); `operationId`/`messageId`
  fields became map keys.

## Workflow

1. Gather semantics first: the application, its brokers, each
   topic/queue, the messages on each with payloads and headers, and which
   direction the application acts in on each channel.
2. Fill `info`, `servers`, then channels (full message sets, parameters
   for any `{expressions}` in addresses), then operations (send/receive
   with message subsets), then message and schema definitions under
   `components`, with a `correlationId` where flows need tracing.
3. Add protocol bindings where broker config is part of the contract.
4. Validate when the CLI is installed; fix errors top-to-bottom, then
   bump `info.version` if this replaces a published document.

## When to open the references

- [references/channels-operations-servers.md](references/channels-operations-servers.md)
  — request-reply (reply objects, dynamic reply addresses), operation and
  message traits, server variables, the full security-scheme type list,
  parameters/address expressions beyond the basics.
- [references/messages-and-schemas.md](references/messages-and-schemas.md)
  — the full multi-format table (Protobuf, OpenAPI, RAML format strings),
  message examples/traits detail, the components map, schema-registry
  pairing.
- [references/bindings.md](references/bindings.md) — Kafka binding fields
  beyond the skeleton (schema registry, topicConfiguration,
  schemaIdLocation), AMQP/MQTT/WebSockets/HTTP bindings.
- [references/style-and-governance.md](references/style-and-governance.md)
  with [assets/spectral-asyncapi.yaml](assets/spectral-asyncapi.yaml) —
  when reviewing someone else's document (checklist), setting up Spectral
  / CI governance, naming conventions, or doing a full v2→v3 migration
  (complete mapping table).
- [assets/template.asyncapi.yaml](assets/template.asyncapi.yaml) — a
  fuller validated example (two-server setup, message traits, licence and
  richer docs) if the skeleton isn't enough.
- Authoritative spec: https://github.com/asyncapi/spec (spec/asyncapi.md);
  protocol bindings: https://github.com/asyncapi/bindings.
