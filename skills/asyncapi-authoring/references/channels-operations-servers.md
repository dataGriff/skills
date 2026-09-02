# Servers, channels, and operations (AsyncAPI 3.1.0)

Field-level detail for the structural half of a document. For messages,
payloads, and schema formats see
[messages-and-schemas.md](messages-and-schemas.md).

## Servers

`servers` is a map of environment name (`^[A-Za-z0-9_\-]+$`) → Server
Object. A server is a broker or endpoint the application connects to.

| Field             | Type   | Notes                                                            |
| ----------------- | ------ | ---------------------------------------------------------------- |
| `host`            | string | **Required.** Hostname, may include port. Supports `{variables}` |
| `protocol`        | string | **Required.** e.g. `kafka`, `amqp`, `mqtt`, `ws`, `http`         |
| `protocolVersion` | string | e.g. `0-9-1` (AMQP), `3.2` (Kafka), `5` (MQTT)                   |
| `pathname`        | string | Path/vhost on the host. Supports `{variables}`                   |
| `title` / `summary` / `description` | string | Say what the environment is *for*          |
| `variables`       | map    | name → Server Variable Object (below)                            |
| `security`        | array  | Security Scheme Objects / $refs — alternatives, one must hold    |
| `tags` / `externalDocs` / `bindings` | —   | as elsewhere                                |

v2 note: v2's single `url` field split into `host` + `protocol` +
`pathname` in v3. There is no `url` field anymore.

```yaml
servers:
  production:
    host: kafka.example.com:9092
    protocol: kafka
    protocolVersion: '3.2'
    description: Production cluster. Requires SASL/SCRAM.
    security:
      - $ref: '#/components/securitySchemes/saslScram'
```

### Server variables

Substituted into `host`/`pathname` wherever `{name}` appears.
Fields: `enum` (list of allowed strings), `default`, `description`,
`examples`. Reusable under `components/serverVariables`.

```yaml
host: '{region}.mq.example.com:5671'
variables:
  region: {enum: [eu-west-1, us-east-1], default: eu-west-1}
```

### Security schemes

Declared under `components/securitySchemes`, referenced from a server's or
operation's `security` array. `type` is required; valid types:
`userPassword`, `apiKey` (with `in: user|password`), `X509`,
`symmetricEncryption`, `asymmetricEncryption`, `httpApiKey` (with `name` +
`in: query|header|cookie`), `http` (with `scheme`, optional
`bearerFormat`), `oauth2` (with `flows`, optional `scopes`), `openIdConnect`
(with `openIdConnectUrl`), and the SASL family: `plain`, `scramSha256`,
`scramSha512`, `gssapi`.

Entries in a `security` array are **alternatives** (OR). Operation-level
security applies *in addition to* server security. Schemes describe the
mechanism only — never embed credentials anywhere in the document.

```yaml
components:
  securitySchemes:
    saslScram:
      type: scramSha512
      description: Provisioned via the platform team's vault role.
```

## Channels

`channels` is a map of channelId → Channel Object. The channelId is a
case-sensitive identifier used by tooling and `$ref`s — follow common
programming naming conventions (this repo's convention: camelCase). The
wire-level name lives in `address`.

| Field         | Type          | Notes                                                          |
| ------------- | ------------- | -------------------------------------------------------------- |
| `address`     | string\|null  | Topic name / routing key / path. `null` or absent = unknown (runtime-determined). May contain `{expressions}`. No query strings or fragments — those go in bindings |
| `messages`    | map           | messageId → Message Object / $ref. **Every** message any app sends to this channel must match exactly one entry |
| `title` / `summary` / `description` | string | —                                        |
| `servers`     | array of $ref | Subset of root servers this channel exists on. Absent/empty = all servers. Must be `$ref`s (e.g. `- $ref: '#/servers/production'`), never inline Server Objects |
| `parameters`  | map           | Required iff `address` contains `{expressions}` (below)        |
| `tags` / `externalDocs` / `bindings` | — | Channel-level broker config (partitions, queue properties) goes in `bindings` |

```yaml
channels:
  userSignedUp:
    address: user.signedup
    description: Fired once per successful signup.
    messages:
      userSignedUp:
        $ref: '#/components/messages/userSignedUp'
```

### Parameters and address expressions

An address may template segments: `address: 'user.{userId}.events'`. Every
expression must have an entry in `parameters` (and vice versa). A Parameter
Object has only `description`, `enum`, `default`, `examples`, and
`location` (a runtime expression such as `$message.payload#/userId` saying
where the value comes from). Parameters are always strings — there is no
`schema` field in v3 (that was v2).

```yaml
channels:
  userEvents:
    address: 'user.{userId}.events'
    parameters:
      userId:
        description: Id of the user this event stream belongs to.
        location: $message.payload#/userId
```

## Operations

`operations` is a map of operationId → Operation Object, listing what
*this application* does. Name operations verb-first from the application's
perspective (`sendOrderPlaced`, `receivePaymentAuthorized`,
`onUserSignedUp`).

| Field      | Type   | Notes                                                                |
| ---------- | ------ | -------------------------------------------------------------------- |
| `action`   | string | **Required.** `send` (this app sends) or `receive` (this app receives) |
| `channel`  | $ref   | **Required.** Must be a Reference Object; root operations must point into root `channels`, never `#/components/...` |
| `messages` | array of $ref | Subset of the channel's messages this operation handles. Refs point *through the channel*: `#/channels/<id>/messages/<id>`. Absent = all channel messages; `[]` = none |
| `reply`    | object | Operation Reply Object for request-reply (below)                     |
| `title` / `summary` / `description` | string | —                                          |
| `security` | array  | Additional schemes required for this operation                       |
| `traits`   | array  | Operation Trait Objects / $refs, merged into the operation (below)   |
| `tags` / `externalDocs` / `bindings` | — | e.g. Kafka `groupId` goes in operation bindings |

```yaml
operations:
  sendUserSignedUp:
    action: send
    channel:
      $ref: '#/channels/userSignedUp'
    summary: Emit an event when a user completes signup.
    messages:
      - $ref: '#/channels/userSignedUp/messages/userSignedUp'
```

### Request-reply

The `reply` field describes the response side of a request-reply exchange.

- Static reply channel: `reply.channel` $refs the channel where replies
  flow, `reply.messages` lists reply messages (refs through that channel).
- Dynamic reply address (e.g. taken from a header): `reply.address` with a
  required `location` runtime expression; the referenced reply channel's
  `address` must then be `null` or absent.

```yaml
operations:
  requestUserDetails:
    action: send
    channel:
      $ref: '#/channels/userRequest'
    reply:
      address:
        description: Reply goes to the topic named in the replyTo header.
        location: '$message.header#/replyTo'
      channel:
        $ref: '#/channels/userReply'      # its address is null
      messages:
        - $ref: '#/channels/userReply/messages/userDetails'
```

Reusable reply objects live in `components/replies` and reply addresses in
`components/replyAddresses`.

### Operation traits

A trait is a partial Operation Object (any field except `action`,
`channel`, `messages`, `traits`) applied via the traits merge mechanism:
traits are merged in order, **last trait wins**, but properties defined on
the operation itself always take precedence over any trait. Use them for
cross-cutting config (shared bindings, common tags). Define under
`components/operationTraits`.

```yaml
operations:
  sendUserSignedUp:
    action: send
    channel: {$ref: '#/channels/userSignedUp'}
    traits:
      - $ref: '#/components/operationTraits/kafkaCommon'
components:
  operationTraits:
    kafkaCommon:
      bindings:
        kafka:
          groupId: {type: string, enum: [signup-service]}
          bindingVersion: 0.5.0
```

## Root vs components — the reference rules

- Root `operations` → must `$ref` root `channels`. Root channels'
  `servers` → must `$ref` root `servers`.
- An operation's / reply's `messages` → must `$ref` messages *of the
  referenced channel* (`#/channels/.../messages/...`), a subset of them.
- Channels' `messages` values → may `$ref` `#/components/messages/...`
  (the usual pattern: define once in components, mount on channels).
- Objects defined under `components` may point at other components
  freely; they affect nothing until referenced from the root.
- `$ref` resolution follows the Reference Object (RFC 3986 URIs) — sibling
  files (`./common.yaml#/components/messages/foo`) work and are how large
  surfaces get split; `asyncapi bundle` merges them back for tools that
  need one file.
