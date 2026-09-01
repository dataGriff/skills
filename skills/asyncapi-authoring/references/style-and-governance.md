# Style, validation, and governance

Conventions that keep a fleet of AsyncAPI documents consistent, and the
tooling that enforces them.

## Naming conventions

The spec only *recommends* "common programming naming conventions" for
identifiers — pick one set per org and enforce it with Spectral. A sound
default (used by this skill's assets):

| Thing                          | Convention               | Example                    |
| ------------------------------ | ------------------------ | -------------------------- |
| channelId / operationId / messageId (map keys) | camelCase | `orderPlaced`, `sendOrderPlaced` |
| operationId shape              | verb-first, app's view   | `sendX`, `receiveX`, `onX` |
| channel `address`              | dot-separated lowercase  | `orders.placed.v1`         |
| `components` keys              | camelCase                | `orderPlacedPayload`       |
| payload property names         | match the wire format — camelCase for JSON, snake_case if your producers emit snake_case; never mix within a doc | |
| server names                   | environment nouns        | `production`, `staging`    |
| file name                      | `asyncapi.yaml` (or `<app>.asyncapi.yaml` in a catalog repo) | |

Address versioning: suffix the *address* (`orders.placed.v1`), not the
channelId — consumers migrate topic by topic.

## Document organization

- **One application per document.** "The order service's API", not "all
  our Kafka topics". A topic shared by many apps appears in each app's
  document (send side in one, receive side in others). For a shared
  catalog, put common messages/schemas in a shared file and `$ref` it
  (`./common/messages.yaml#/components/messages/orderPlaced`), then
  `asyncapi bundle` when a tool needs a single file.
- Root `channels`/`operations` are the application's actual surface;
  drafts and shared-but-unused definitions live under `components`.
- Always fill `info.description` and `info.contact` — a document without
  an owner is unmaintainable in a catalog.

## Versioning policy

- `info.version` is the application API's semver. Breaking (major):
  removing/renaming a channel address or field consumers rely on,
  narrowing a payload type, changing a key or correlation scheme.
  Additive (minor): new channel, new optional field, new example. Docs-only
  (patch).
- `asyncapi: 3.1.0` changes only when adopting a newer spec release.
- `asyncapi diff old.yaml new.yaml -t breaking` catches accidental
  breaking changes in CI.

## Validation

Two layers, both in CI:

1. **Spec validation** — AsyncAPI CLI (`npm i -g @asyncapi/cli`):

   ```bash
   asyncapi validate asyncapi.yaml
   asyncapi validate asyncapi.yaml --diagnostics-format=json  # machine output
   ```

   The parser validates against the meta-schema plus semantic rules
   (unresolvable `$ref`s, operations pointing outside root channels, …).

2. **Org style** — Spectral (`npm i -g @stoplight/spectral-cli`):

   ```bash
   spectral lint --ruleset spectral-asyncapi.yaml asyncapi.yaml
   ```

   Start from [../assets/spectral-asyncapi.yaml](../assets/spectral-asyncapi.yaml).
   `extends: spectral:asyncapi` gives the built-in ruleset (covers v2 and
   v3 documents; rules are tagged per version internally); custom rules
   add org conventions on top.

Useful CLI extras: `asyncapi bundle` (merge multi-file docs),
`asyncapi convert` (version upgrades), `asyncapi diff`,
`asyncapi generate models <lang>` (typed payload models),
`asyncapi start studio` (visual editor).

## Writing custom Spectral rules for v3

Target v3 paths explicitly; `given` uses JSONPath:

```yaml
rules:
  channel-address-lowercase:
    description: Channel addresses are dot-separated lowercase.
    severity: error
    given: $.channels[*].address
    then:
      function: pattern
      functionOptions:
        match: '^[a-z0-9]+([.{][a-zA-Z0-9}]+)*$'
  operation-has-summary:
    description: Every operation explains itself.
    severity: warn
    given: $.operations[*]
    then:
      field: summary
      function: truthy
```

Common org rules worth writing: required `info.contact`, camelCase map
keys (`$.channels`, `$.operations` with the `casing` function on `@key`),
pinned `bindingVersion` (not `latest`), every message has `examples`,
every server has `description`, forbid `x-` extensions outside an approved
list.

## Review checklist

When asked to review an AsyncAPI document, check in order:

1. **Version & validity** — `asyncapi: 3.x`? Does `asyncapi validate`
   pass? v2 tells: `publish`/`subscribe` under channels, server `url`,
   channel keys that are addresses (`user/{id}/signedup`), `parameters`
   with `schema`, message `messageId` field, `components.schemas` using
   `schemaFormat` at message level only.
2. **Semantics** — do operations describe the *application's* actions
   (send = it sends)? Is every channel message set complete and mutually
   distinguishable? Operation `messages` a subset of the channel's?
3. **Secrets** — no credentials in hosts, variables, examples, or
   bindings. `user:pass@host` is a blocking defect.
4. **Completeness** — owner contact, server descriptions, message
   summaries + examples, correlation IDs on traced flows, bindings pinned.
5. **Conventions** — naming per org ruleset; Spectral clean.

## Migrating v2 → v3

`asyncapi convert asyncapi.yaml -f asyncapi -t 3.0.0` mechanizes most of
this; always review the output. The mapping:

| v2                                      | v3                                                        |
| --------------------------------------- | --------------------------------------------------------- |
| channel key doubles as address          | channelId key + explicit `address`                        |
| `subscribe` operation ("others may subscribe" = **this app sends**) | root operation `action: send` |
| `publish` operation ("others may publish" = **this app receives**)  | root operation `action: receive` |
| `operationId` field                     | the operation's map key                                   |
| `message.oneOf`                         | the channel `messages` map (already one-of)               |
| `messageId` field                       | the message's map key                                     |
| server `url: kafka://host:9092/path`    | `host`, `protocol`, `pathname` fields                     |
| server `security: [{scheme: []}]` name+scopes form | `security` array of $refs to scheme objects; scopes move into the scheme's `scopes` |
| parameter `schema`                      | gone — parameters are strings with `enum`/`default`/`examples` |
| `schemaFormat` on the message           | Multi Format Schema Object on the payload itself          |

The `publish`/`subscribe` inversion is the trap: v2 documents were written
from the *client's* perspective. When converting by hand, re-derive each
operation's `action` from what the application actually does — don't
map keywords mechanically. If the doc you're editing must stay on v2
(tooling constraints), keep v2 semantics — don't mix.
