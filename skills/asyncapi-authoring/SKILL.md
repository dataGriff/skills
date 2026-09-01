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

Write event-driven API definitions against **AsyncAPI 3.1.0**
(`asyncapi: 3.1.0`). One document describes one *application* — the thing
that connects to brokers and sends or receives messages — conventionally
saved as `asyncapi.yaml`. 3.1.0 is structurally identical to 3.0.0 (it adds
ROS 2 bindings), so 3.0 guidance applies unchanged; prefer 3.1.0 for new
documents.

Start from [assets/template.asyncapi.yaml](assets/template.asyncapi.yaml) —
copy it and adapt rather than writing from a blank page. Validate with
`asyncapi validate <file>` (AsyncAPI CLI, `npm i -g @asyncapi/cli`).

## The shape of a document

```yaml
asyncapi: 3.1.0           # spec version — always 3.1.0 for new documents
info: {title, version, description, contact, ...}   # required
servers:                  # brokers/environments: host + protocol per entry
  production: {host, protocol, ...}
channels:                 # WHERE messages flow: address + the messages on it
  orderPlaced:
    address: orders.placed
    messages: {orderPlaced: {$ref: '#/components/messages/orderPlaced'}}
operations:               # WHAT this app does: send or receive on a channel
  publishOrderPlaced:
    action: send
    channel: {$ref: '#/channels/orderPlaced'}
components:               # reusable definitions, inert until $ref'd
  messages: {...}
  schemas: {...}
defaultContentType: application/json
```

Only `asyncapi` and `info` (with `title` + `version`) are required — but a
useful document declares its servers, every channel the application
touches, and an operation for each thing the application actually does.

## The v3 mental model — get this right first

- **Channels say *where*, operations say *what*.** A channel is an
  addressable place (topic, queue, path) plus the messages that flow over
  it. An operation is this application's use of a channel: `action: send`
  or `action: receive`. In v2 these were fused (`publish`/`subscribe`
  under the channel) and notoriously inverted; in v3 there is no ambiguity.
- **The document describes *this application's* behavior, not the
  reader's.** `action: send` means the described application sends.
  Consumers reading the document invert it for themselves.
- **Channel keys are identifiers, addresses are the wire truth.** The map
  key (`orderPlaced`) is a case-sensitive id for tooling and `$ref`s; the
  `address` (`orders.placed`) is the actual topic/routing key/path. Never
  put the address in the key.
- **Root = implemented, components = available.** Channels and operations
  at the document root MUST exist / be implemented by the application.
  Anything under `components` is inert until referenced. Root operations
  must `$ref` root channels (never `#/components/...`); a root channel's
  `servers` list must `$ref` root servers.
- **Reuse via `$ref`.** Define messages and schemas once under
  `components`, reference them from channels; an operation's `messages`
  list points *through the channel* (`#/channels/orderPlaced/messages/...`),
  not into components.

## Workflow

1. **Gather semantics before syntax.** Identify the application being
   described, the brokers/environments it connects to, each topic/queue it
   uses, the messages on each, their payloads and headers, and which
   direction the application acts in (send vs receive) on each channel.
2. **Write `info`** — title naming the application (not the broker),
   semver `version` of the API, description, contact/owner.
3. **Declare `servers`** — one per environment, `host` + `protocol`
   (+ `protocolVersion`, `security`, variables). Read
   [references/channels-operations-servers.md](references/channels-operations-servers.md)
   for server fields, variables, and security schemes.
4. **Model `channels`** — one per topic/queue/path, with `address`, the
   full set of `messages` valid on it, `parameters` for any `{expressions}`
   in the address, and protocol `bindings` where broker config matters
   (partitions, queue durability). Same reference covers channel fields,
   parameters, and the root-vs-components rules.
5. **Declare `operations`** — one per send/receive the application
   performs, with `action`, a `channel` $ref, and a `messages` subset when
   the operation handles fewer messages than the channel carries. Use
   `reply` for request-reply. Same reference covers operations, traits,
   and reply objects.
6. **Define messages and payloads under `components`.** Give each message
   a `name`, `title`, `summary`, payload schema, `examples`, and a
   `correlationId` where flows need tracing. Payloads default to AsyncAPI
   Schema Object (JSON Schema draft 7 superset); use a multi-format schema
   (`schemaFormat` + `schema`) for Avro or Protobuf. Read
   [references/messages-and-schemas.md](references/messages-and-schemas.md)
   for message fields, traits, correlation IDs, and schema formats.
7. **Add protocol bindings** at whichever level the protocol detail lives
   (server, channel, operation, message) — e.g. Kafka `key` on the message,
   `groupId` on the operation. Read
   [references/bindings.md](references/bindings.md) for the Kafka fields
   and the pattern for other protocols.
8. **Validate.** `asyncapi validate <file>`. Fix errors top-to-bottom.
9. **Enforce conventions with Spectral.** Schema validation accepts an
   undescribed server and a camelCase-vs-kebab mess; org style rules need
   a Spectral ruleset — start from
   [assets/spectral-asyncapi.yaml](assets/spectral-asyncapi.yaml)
   (extends `spectral:asyncapi`, which covers v2 and v3) and run both in
   CI. Read
   [references/style-and-governance.md](references/style-and-governance.md)
   for naming conventions, custom rules, versioning, and v2→v3 migration.

## Authoring judgment

- **`info.version` ≠ `asyncapi` version.** Bump `info.version` (semver) on
  API changes: major for breaking (removed channel/field, renamed address,
  narrowed payload), minor for additive. The `asyncapi` field only changes
  when adopting a newer spec release.
- **Model the full channel, then narrow per operation.** A channel's
  `messages` map is everything any application may put on it; an
  operation's `messages` list is the subset this application handles.
  Omitting the operation's list means "all of them" — set it explicitly
  when narrowing, and `[]` means none.
- **Every message on a channel must match exactly one message object** —
  make payloads distinguishable (a discriminating field or distinct
  required sets), or tooling can't tell them apart.
- **Bindings carry protocol truth; keep the rest portable.** Business
  meaning lives in messages, schemas, and descriptions. Broker specifics
  (partitions, groupIds, schema-registry wiring) live in bindings — and
  pin `bindingVersion` rather than relying on `latest`.
- **Never invent top-level or object fields.** Org-specific metadata goes
  in specification extensions (`x-` prefixed keys, valid on any object) —
  anything else fails validation.
- **No secrets.** Server definitions carry hosts and security *scheme*
  descriptions (the *how*, e.g. `scramSha512`), never credentials.
  Usernames/passwords in an `amqp://user:pass@host` style URL are a
  review-blocking defect.
- **Upgrading v2 documents is a restructure, not a rename.** `publish` in
  v2 meant "others may publish; this app receives" — carrying it to
  `action: send` silently inverts the API. Follow the migration table in
  [references/style-and-governance.md](references/style-and-governance.md),
  or run `asyncapi convert` and review its output.

## References

- [references/channels-operations-servers.md](references/channels-operations-servers.md)
  — servers, server variables, security schemes, channels, parameters and
  address expressions, operations, traits, request-reply.
- [references/messages-and-schemas.md](references/messages-and-schemas.md)
  — message objects, headers/payload, correlation IDs and runtime
  expressions, message traits and examples, multi-format schemas
  (Avro/Protobuf/JSON Schema), schema object fields.
- [references/bindings.md](references/bindings.md) — how bindings work at
  all four levels; Kafka bindings in detail; AMQP, MQTT, WebSockets, HTTP
  in brief; version pinning.
- [references/style-and-governance.md](references/style-and-governance.md)
  — naming conventions, document organization, validation and CI, Spectral
  rulesets, versioning policy, v2→v3 migration table.
- [assets/template.asyncapi.yaml](assets/template.asyncapi.yaml) — a
  complete, valid starter document to copy.
- [assets/spectral-asyncapi.yaml](assets/spectral-asyncapi.yaml) — starter
  governance ruleset extending `spectral:asyncapi`.
- Authoritative spec: https://github.com/asyncapi/spec (spec/asyncapi.md)
  and https://www.asyncapi.com/docs/reference/specification/latest —
  consult for anything not covered here. Protocol bindings live in
  https://github.com/asyncapi/bindings.
