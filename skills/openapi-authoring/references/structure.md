# Document structure: root, paths, operations, responses

## Root object

| Field | Notes |
| --- | --- |
| `openapi` | Required. `3.1.0` (or `3.1.1`) for new documents. |
| `info` | Required. See below. |
| `jsonSchemaDialect` | Default dialect for schemas; omit unless you need a non-default one. |
| `servers` | Base URLs. Defaults to `[{url: /}]` if omitted. |
| `paths` | The API surface. |
| `webhooks` | Named out-of-band requests the API sends (new in 3.1). |
| `components` | All reusable objects (see schemas-and-components.md). |
| `security` | Default security requirements for every operation (see security.md). |
| `tags` | Declare every tag used by operations, with descriptions — doc tools use this list for ordering and navigation. |
| `externalDocs` | Link to prose documentation. |

At least one of `paths`, `components`, or `webhooks` must be present.

## Info

`title` and `version` are required. Always also write a `description`
(CommonMark) saying what the API is for and who consumes it. Optional:
`summary` (3.1), `termsOfService`, `contact` (`name`/`url`/`email`), and
`license` — in 3.1 `license.identifier` takes an SPDX id (`Apache-2.0`),
mutually exclusive with `license.url`.

## Servers

```yaml
servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://{env}.api.example.com/v1
    description: Pre-production environments
    variables:
      env:
        default: staging
        enum: [staging, dev]
```

Paths are appended to the server URL, so version prefixes belong here, not
repeated in every path. Operations and path items may declare their own
`servers` to override the global list.

## Paths and path items

Keys are URL templates relative to the server URL: `/orders/{orderId}`.
Template expressions cover exactly one segment; every expression must have a
matching path parameter. Identical templates that differ only by parameter
name are duplicates. A path item holds the HTTP methods (`get`, `put`,
`post`, `delete`, `options`, `head`, `patch`, `trace`), plus `summary`,
`description`, `servers`, and `parameters` shared by all its operations.

## Operations

```yaml
get:
  operationId: listOrders        # unique across the whole document
  summary: List orders
  description: Optional longer CommonMark prose.
  tags: [orders]
  parameters:
    - $ref: "#/components/parameters/PageSize"
  responses: {...}
  security: [...]                # override the global default if needed
  deprecated: true               # keep deprecated operations documented
```

Give every operation an `operationId` (camelCase verb phrase —
`listOrders`, `getOrder`, `cancelOrder`): generators turn it into client
method names, and Spectral rules key off it. `summary` is the one-liner doc
tools show in navigation; don't leave it empty.

## Parameters

```yaml
parameters:
  - name: orderId
    in: path                # path | query | header | cookie
    required: true          # path parameters MUST be required: true
    description: Order identifier.
    schema:
      type: string
      format: uuid
  - name: status
    in: query
    schema:
      type: array
      items: {type: string, enum: [pending, paid, shipped]}
    style: form             # default for query; form + explode: true → status=a&status=b
    explode: true
```

Uniqueness is `name` + `in`. Use `schema` for parameters (the normal case);
`content: {media-type: {schema}}` only when the parameter itself is a
serialized document (e.g. JSON in a query param). Reusable parameters
(pagination, common filters, tenant headers) go in `components/parameters`
and are `$ref`'d. Don't define `Accept`, `Content-Type`, or `Authorization`
as header parameters — the first two are driven by `content` maps, the last
by `securitySchemes`.

## Request bodies

```yaml
requestBody:
  required: true            # default is false — set it explicitly for writes
  description: Order to create.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/OrderCreate"
      examples:
        minimal:
          value: {customerId: "…", items: [{sku: "A-1", quantity: 2}]}
```

`content` maps media type → schema. Use distinct schemas for create/update
inputs vs. the resource representation (server-set fields like `id` and
`createdAt` don't belong in the create body). `GET`/`DELETE` requests
should not carry bodies.

## Responses

```yaml
responses:
  "200":
    description: The order.            # description is required on every response
    content:
      application/json:
        schema: {$ref: "#/components/schemas/Order"}
  "404": {$ref: "#/components/responses/NotFound"}
  default: {$ref: "#/components/responses/Error"}
```

Status codes are quoted strings; ranges like `"4XX"` are allowed; `default`
catches everything undeclared — point it at the shared error response.
Document response headers under `headers` (e.g. `Location` on 201,
`Retry-After` on 429) — header names there must not include `Content-Type`.
A 204 has no `content`. `links` on a response can name follow-up operations
(`operationId` + parameter mapping) for HATEOAS-style navigation — useful
but optional.

## Webhooks

Top-level `webhooks` is a map of event name → path item, describing
requests the API *sends* to subscribers; the consumer implements them.
Shape is identical to a path item, so request bodies and expected responses
are modelled the same way:

```yaml
webhooks:
  orderShipped:
    post:
      operationId: onOrderShipped
      requestBody:
        content:
          application/json:
            schema: {$ref: "#/components/schemas/OrderShippedEvent"}
      responses:
        "200": {description: Acknowledged.}
```
