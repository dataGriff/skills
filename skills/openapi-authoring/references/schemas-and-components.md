# Schemas and components

## Components

Every reusable object lives under `components`, keyed by name
(`^[a-zA-Z0-9._-]+$`), referenced via `$ref`:

```yaml
components:
  schemas: {...}          # $ref: "#/components/schemas/Order"
  parameters: {...}
  responses: {...}
  requestBodies: {...}
  headers: {...}
  examples: {...}
  links: {...}
  callbacks: {...}
  pathItems: {...}        # new in 3.1
  securitySchemes: {...}  # see security.md
```

Name schemas in UpperCamelCase after the resource (`Order`, `OrderCreate`,
`Problem`) — these names become generated class names. Defining a schema in
components does nothing by itself; it must be referenced. In 3.1 a `$ref`
may sit alongside `summary`/`description` to override the target's docs;
other sibling keywords next to `$ref` are ignored by many tools — restructure
with `allOf` instead.

## Schema objects are JSON Schema 2020-12

In 3.1 the schema object is full JSON Schema draft 2020-12 — no more
"subset". The everyday fields:

```yaml
Order:
  type: object
  description: A customer order.
  required: [id, status, totalAmount]
  properties:
    id: {type: string, format: uuid}
    status:
      type: string
      enum: [pending, paid, shipped, cancelled]
    totalAmount:
      type: number
      minimum: 0
    couponCode:
      type: [string, "null"]        # nullable in 3.1: a type array with "null"
      maxLength: 20
    items:
      type: array
      minItems: 1
      items: {$ref: "#/components/schemas/OrderItem"}
  additionalProperties: false        # decide explicitly; default is open
  examples:                          # JSON Schema keyword — array, no names
    - {id: "…", status: paid, totalAmount: 12.5, items: [...]}
```

- `required` lists property names; there is no per-property `required`.
- Constraints: `minLength`/`maxLength`/`pattern` (strings), `minimum`/
  `maximum`/`exclusiveMinimum`/`exclusiveMaximum` (numbers — in 3.1 the
  exclusive forms take a **number**, not a boolean), `minItems`/`maxItems`/
  `uniqueItems` (arrays), `minProperties`/`maxProperties`.
- `format` is an annotation, not validation: `date-time`, `date`, `uuid`,
  `uri`, `email`, `int32`, `int64`, `float`, `double`. Add `pattern` when a
  format must actually be enforced.
- `const` fixes a single value (better than a one-value `enum`).
- `readOnly: true` marks server-set fields (returned, never accepted) — an
  alternative to separate create/read schemas for simple cases;
  `writeOnly: true` the reverse (e.g. passwords).
- `default` documents what the server assumes when a field is omitted.

## Composition and polymorphism

- **`allOf`** — intersection; the standard "extend a base schema" idiom:

  ```yaml
  AdminUser:
    allOf:
      - $ref: "#/components/schemas/User"
      - type: object
        required: [permissions]
        properties:
          permissions: {type: array, items: {type: string}}
  ```

- **`oneOf`** — exactly one branch matches; use for unions/variants. Add a
  `discriminator` so tools and readers can dispatch without trial matching:

  ```yaml
  PaymentMethod:
    oneOf:
      - $ref: "#/components/schemas/CardPayment"
      - $ref: "#/components/schemas/BankTransfer"
    discriminator:
      propertyName: kind
      mapping:
        card: "#/components/schemas/CardPayment"
        bank: "#/components/schemas/BankTransfer"
  ```

  Each branch must be an object schema that itself requires the
  discriminator property.
- **`anyOf`** — one or more match; rarely what an API contract means.
  Prefer `oneOf`.
- Avoid deep `not`/conditional (`if`/`then`) logic in public contracts —
  valid JSON Schema, but many generators ignore it silently.

## Binary and file payloads

3.1 replaced `format: byte/binary` with content hints:

```yaml
# Raw upload/download: schema is optional — the media type says it all
content:
  application/octet-stream: {}
  image/png: {}
# Base64-embedded in JSON:
avatar: {type: string, contentEncoding: base64, contentMediaType: image/png}
# Multipart form upload:
content:
  multipart/form-data:
    schema:
      type: object
      properties:
        file: {type: string, contentMediaType: application/pdf}
        caption: {type: string}
```

## Media-type examples

Alongside `schema`, a media type object takes `example` (one, unnamed) or
`examples` (named map — each entry has `summary` and `value`, or
`externalValue` for a URL). Named `examples` render as a picker in docs and
seed mock servers; supply one per interesting variant (each `oneOf` branch,
empty list vs. populated). Note the JSON Schema keyword inside schemas is
also spelled `examples` but is a plain array of values.

## Migrating 3.0 → 3.1

| 3.0 | 3.1 |
| --- | --- |
| `nullable: true` | `type: [T, "null"]` |
| `exclusiveMinimum: true` + `minimum: n` | `exclusiveMinimum: n` |
| schema `example: v` (singular) | `examples: [v]` (singular still tolerated, deprecated) |
| `type: string, format: byte/binary` | `contentEncoding` / `contentMediaType` / bare media type |
| single `type` string only | type arrays allowed |
| no top-level `webhooks` | `webhooks` map |
| `license.url` only | `license.identifier` (SPDX) |

Bump `openapi: 3.0.x` → `3.1.0` only together with these rewrites —
`nullable` is silently meaningless in 3.1, which turns previously-nullable
fields into never-null contracts.
