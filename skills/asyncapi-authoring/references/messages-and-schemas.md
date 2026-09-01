# Messages and schemas (AsyncAPI 3.1.0)

Field-level detail for messages, payloads, and schema formats. For the
channels/operations they attach to, see
[channels-operations-servers.md](channels-operations-servers.md).

## Message Object

Usually defined under `components/messages` and `$ref`'d from channels.

| Field           | Type   | Notes                                                            |
| --------------- | ------ | ---------------------------------------------------------------- |
| `payload`       | schema | Schema Object, Multi Format Schema Object, or $ref (below)       |
| `headers`       | schema | Application headers only — a map of key→value. Never protocol headers (those belong in bindings) |
| `correlationId` | object | Correlation ID Object or $ref (below)                            |
| `contentType`   | string | Media type, e.g. `application/json`, `avro/binary`. Falls back to root `defaultContentType` |
| `name`          | string | Machine-friendly name (e.g. the event type on the wire)          |
| `title` / `summary` / `description` | string | Human docs — always give at least a summary |
| `examples`      | array  | Message Example Objects (below)                                  |
| `traits`        | array  | Message Trait Objects / $refs, merged (below)                    |
| `tags` / `externalDocs` / `bindings` | — | e.g. Kafka message `key` goes in bindings   |

There is no `messageId` *field* — the message's identifier is its map key
(in `components/messages` or a channel's `messages` map), case-sensitive.

```yaml
components:
  messages:
    orderPlaced:
      name: OrderPlaced
      title: Order placed
      summary: A customer completed checkout and an order was created.
      contentType: application/json
      correlationId:
        location: '$message.header#/correlationId'
      headers:
        type: object
        properties:
          correlationId: {type: string, format: uuid}
      payload:
        $ref: '#/components/schemas/orderPlacedPayload'
      examples:
        - name: minimal
          summary: Smallest valid order
          payload: {orderId: 9dbc3d5e-..., total: 12.5, currency: EUR}
```

## Correlation IDs and runtime expressions

A Correlation ID Object marks where the value used to trace/match messages
lives: `location` (**required**, a runtime expression) + optional
`description`. Reusable under `components/correlationIds`.

Runtime expressions address a location *within this message*:

- `$message.header#/MQMD/CorrelId` — JSON Pointer into the headers.
- `$message.payload#/user/id` — JSON Pointer into the payload.

The same expression syntax powers `reply.address.location` and a channel
parameter's `location`.

## Message examples

Each entry in `examples` must have `headers` and/or `payload` (concrete
values, matching the schemas), plus optional `name` and `summary`. Good
examples are the cheapest documentation a message can have — include at
least one per message, and one per meaningfully different variant.

## Message traits

A trait is a partial Message Object (any field except `payload` and
`traits`) — use for shared headers, `contentType`, correlation IDs across
messages. Defined under `components/messageTraits`, applied via `traits:`.
Merge rules: applied in order, last trait wins, but fields set directly on
the message always win over traits.

```yaml
components:
  messageTraits:
    commonHeaders:
      headers:
        type: object
        properties:
          correlationId: {type: string, format: uuid}
      correlationId:
        location: '$message.header#/correlationId'
```

## Payload schemas

### Default: the AsyncAPI Schema Object

With no `schemaFormat`, `payload`/`headers` are AsyncAPI Schema Objects —
a **superset of JSON Schema draft 07**. All draft-07 keywords work
(`type`, `required`, `properties`, `enum`, `const`, `pattern`, `format`,
`oneOf`/`allOf`/`anyOf`/`not`, `if`/`then`/`else`, `additionalProperties`,
…) plus AsyncAPI's `discriminator` (polymorphism; the named property must
be in `required`), `externalDocs`, and `deprecated`. `true`/`false` are
valid schemas (anything / nothing).

Schema style guidance:

- Describe every property; give `format` where it exists (`date-time`,
  `uuid`, `email`, `int64`).
- Constrain: `required`, `enum` for closed sets, `additionalProperties:
  false` when the producer guarantees a closed payload.
- Share subobjects via `components/schemas` + `$ref` — note `$ref` here
  follows AsyncAPI's Reference Object semantics (siblings ignored), not
  full JSON Schema `$ref`.

### Other formats: the Multi Format Schema Object

Anywhere a schema is allowed, you may instead give an object with
`schemaFormat` (**required**) and `schema` (**required**):

```yaml
payload:
  schemaFormat: 'application/vnd.apache.avro;version=1.9.0'
  schema:
    type: record
    name: UserCreated
    namespace: com.example
    fields:
      - {name: userId, type: string}
      - {name: age, type: int}
```

Format strings tools must/should support:

| Format                    | `schemaFormat` value                                            |
| ------------------------- | --------------------------------------------------------------- |
| AsyncAPI Schema (default) | `application/vnd.aai.asyncapi;version=3.1.0` (+`+json`/`+yaml`) |
| JSON Schema draft-07      | `application/schema+json;version=draft-07` (or `+yaml`)         |
| Avro 1.9.0                | `application/vnd.apache.avro;version=1.9.0` (+`+json`/`+yaml`)  |
| OpenAPI 3.0 Schema        | `application/vnd.oai.openapi;version=3.0.0` (+`+json`/`+yaml`)  |
| RAML 1.0 data type        | `application/raml+yaml;version=1.0`                             |
| Protobuf 2 / 3            | `application/vnd.google.protobuf;version=2` or `;version=3`     |

Rules that bite:

- JSON-based schemas (Avro included) are inlined as YAML/JSON *objects*;
  non-JSON schemas (Protobuf, XSD) are inlined as a *string*.
- A `$ref` inside a multi-format schema must resolve to a resource of the
  **same** `schemaFormat` — pointing an Avro schema at a JSON Schema file
  is invalid. External files work: `schema: {$ref: './user.avsc'}`.
- Pair the format with a matching `contentType` on the message
  (e.g. Avro + `avro/binary`) so codegen and validation agree.
- When a message's schema lives in a schema registry, still describe the
  payload in the document (inline or `$ref` to the `.avsc`) and wire the
  registry itself via Kafka server bindings (`schemaRegistryUrl`) — see
  [bindings.md](bindings.md).

## Components map — what can be reused

`components` holds maps (keys matching `^[a-zA-Z0-9\.\-_]+$`) of:
`schemas`, `servers`, `channels`, `operations`, `messages`,
`securitySchemes`, `serverVariables`, `parameters`, `correlationIds`,
`replies`, `replyAddresses`, `externalDocs`, `tags`, `operationTraits`,
`messageTraits`, `serverBindings`, `channelBindings`, `operationBindings`,
`messageBindings`. Everything here is inert until referenced. Org-specific
metadata goes in `x-` specification extensions on any object — never
invented fields.
