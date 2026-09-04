---
name: openapi-authoring
description: >-
  Author, edit, and review OpenAPI (Swagger) API descriptions — OpenAPI 3.1
  YAML/JSON. Covers document structure, info/servers/tags, paths and
  operations, parameters, request and response bodies, reusable components,
  JSON Schema 2020-12 modelling (composition, discriminators, nullability),
  security schemes (API key, bearer, OAuth2, OIDC, mTLS), examples,
  webhooks, RFC 9457 error responses, pagination, versioning, 3.0-to-3.1
  migration, and enforcing org style rules with Spectral rulesets. Use when
  the user wants to create or modify an OpenAPI or Swagger spec, mentions
  openapi.yaml / swagger.json, asks to design or document a REST API, add
  endpoints, schemas, auth, or examples to a spec, review a spec for
  completeness or convention compliance, lint with Spectral or Redocly, or
  upgrade a spec between OpenAPI versions — even if they just say "write an
  API spec for X".
---

# Authoring OpenAPI descriptions

An API description is one YAML document against **OpenAPI 3.1**
(`openapi: 3.1.0`), conventionally `openapi.yaml` (or `<api>.openapi.yaml`
when a repo holds several). Never start a new spec on 3.0 or Swagger 2.0;
use 3.2 only when the user's toolchain is confirmed on it. The skeleton
below carries the syntax for everything a useful spec needs; work from it
directly and open the references only for the cases listed at the end.
Validate with `spectral lint <file>` when Spectral is installed (its
built-in `spectral:oas` ruleset also catches structural errors);
`redocly lint` is an equivalent alternative.

## The skeleton

```yaml
openapi: 3.1.0
info:
  title: Orders API
  version: 1.0.0            # the API's semver, not the spec's
  description: Create and track customer orders.
servers:
  - url: https://api.example.com/v1   # major version lives here, not in paths
tags:
  - name: orders
    description: Customer order lifecycle.
security:
  - bearerAuth: []          # secure by default; override per operation
paths:
  /orders:
    get:
      operationId: listOrders   # unique camelCase; becomes client method names
      summary: List orders
      tags: [orders]
      parameters:
        - name: pageSize
          in: query
          schema: {type: integer, minimum: 1, maximum: 100, default: 20}
        - name: pageToken
          in: query
          description: Cursor from a previous page's nextPageToken.
          schema: {type: string}
      responses:
        "200":
          description: One page of orders.
          content:
            application/json:
              schema:
                type: object    # wrap lists; a bare array can't grow metadata
                required: [items]
                properties:
                  items: {type: array, items: {$ref: "#/components/schemas/Order"}}
                  nextPageToken: {type: [string, "null"]}
        default: {$ref: "#/components/responses/Error"}
    post:
      operationId: createOrder
      summary: Create an order
      tags: [orders]
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: "#/components/schemas/OrderCreate"}
      responses:
        "201":
          description: The created order.
          content:
            application/json:
              schema: {$ref: "#/components/schemas/Order"}
        "422": {$ref: "#/components/responses/UnprocessableEntity"}
        default: {$ref: "#/components/responses/Error"}
  /orders/{orderId}:
    parameters:
      - name: orderId
        in: path
        required: true            # path parameters are always required: true
        description: Order identifier.
        schema: {type: string, format: uuid}
    get:
      operationId: getOrder
      summary: Get an order
      tags: [orders]
      responses:
        "200":
          description: The order.
          content:
            application/json:
              schema: {$ref: "#/components/schemas/Order"}
        "404": {$ref: "#/components/responses/NotFound"}
        default: {$ref: "#/components/responses/Error"}
components:
  securitySchemes:
    bearerAuth: {type: http, scheme: bearer, bearerFormat: JWT}
  schemas:                    # UpperCamelCase names — they become class names
    OrderCreate:
      type: object
      description: Payload to create an order; server-set fields excluded.
      required: [customerId, items]
      properties:
        customerId: {type: string, format: uuid}
        items:
          type: array
          minItems: 1
          items:
            type: object
            required: [sku, quantity]
            properties:
              sku: {type: string}
              quantity: {type: integer, minimum: 1}
        couponCode:
          type: [string, "null"]  # nullable in 3.1: a type array with "null"
    Order:
      allOf:                      # composition: extend the create payload
        - $ref: "#/components/schemas/OrderCreate"
        - type: object
          required: [id, status, totalAmount]
          properties:
            id: {type: string, format: uuid, readOnly: true}
            status: {type: string, enum: [pending, paid, shipped, cancelled]}
            totalAmount: {type: number, minimum: 0}
    Problem:
      type: object
      description: RFC 9457 problem details.
      properties:
        type: {type: string, format: uri, default: "about:blank"}
        title: {type: string}
        status: {type: integer}
        detail: {type: string}
  responses:                  # shared error responses, $ref'd everywhere
    NotFound:
      description: The resource does not exist.
      content:
        application/problem+json:
          schema: {$ref: "#/components/schemas/Problem"}
    UnprocessableEntity:
      description: Well-formed but semantically invalid request.
      content:
        application/problem+json:
          schema: {$ref: "#/components/schemas/Problem"}
    Error:
      description: Unexpected error.
      content:
        application/problem+json:
          schema: {$ref: "#/components/schemas/Problem"}
```

Only `openapi`, `info`, and one of `paths`/`components`/`webhooks` are
required — but a spec that stops there documents nothing. A useful spec
describes every response a client can receive (errors included), models
bodies as named component schemas, and declares how callers authenticate.

## Rules that matter

- **Naming.** Plural kebab-case resource paths, no verbs (actions become
  sub-resources: `POST /orders/{orderId}/cancel`); camelCase parameters,
  properties, and operationIds; UpperCamelCase schema names.
- **Every response documented.** The success code with its schema, the 4xx
  codes that apply, and a `default` pointing at the shared error response.
  Errors are one `Problem` model (`application/problem+json`), never
  per-endpoint ad-hoc bodies.
- **Prefer `$ref` over repetition.** Non-trivial bodies are named schemas
  under `components`; repeated parameters, headers, and responses live
  there too — inline copies drift and can't be targeted by codegen.
- **Security semantics.** Entries in a `security` list are OR; keys within
  one entry are AND; the array value carries scopes only for
  oauth2/openIdConnect schemes. An operation-level `security` replaces the
  global default entirely; `security: []` means deliberately public. Never
  put credential values or example tokens anywhere in a spec.
- **3.0 → 3.1 traps** when touching older specs: `nullable: true` becomes
  `type: [T, "null"]`; `exclusiveMinimum` takes a number, not a boolean;
  schema `example:` becomes the `examples:` array; `format: byte/binary`
  becomes `contentEncoding`/`contentMediaType` or a bare media type. A
  version bump without these rewrites silently changes the contract.
- **`info.version` is the API's version, not the spec's.** Bump it semver:
  major for breaking (removed/renamed field or operation, tightened
  validation, new required parameter), minor for additive. Design so
  growth is non-breaking: optional new fields, no repurposing.
- **The spec is the contract, not a code dump.** Describe what a client
  can rely on; don't mirror internal DB columns or leak implementation
  names — this holds when reviewing generated specs too.

## Workflow

1. Model resources before routes: identify the nouns, their lifecycle
   (create/read/list/update/delete/transitions), who calls them and how
   they authenticate. URLs invented first tend to become verbs.
2. Write info (title, semver version, real description), servers per
   environment, tags with descriptions; then one path item per URL
   template, each operation with operationId, summary, and a complete
   responses map.
3. Model bodies as named component schemas; define security schemes and a
   global default; add named examples where behaviour isn't obvious (one
   per `oneOf` branch — mocks and docs surface them directly).
4. Lint and fix top-to-bottom; warnings are usually worth fixing too.
5. When the spec should gate or unblock development — serving its
   examples as live mocks for consumers, or verifying an implementation
   conforms in CI — hand over to the `api-mocking-microcks` /
   `contract-testing-microcks` skills (where available).

## When to open the references

- [references/structure.md](references/structure.md) — parameter
  styles/explode, header/cookie parameters, response headers and links,
  server variables, webhooks, request-body nuances.
- [references/schemas-and-components.md](references/schemas-and-components.md)
  — `oneOf`/`discriminator` polymorphism, binary and multipart payloads,
  media-type examples, the full 3.0→3.1 migration table, all components
  sections.
- [references/security.md](references/security.md) — OAuth2 flow and scope
  definitions, apiKey/OIDC/mTLS schemes, multi-scheme requirements.
- [references/style-and-governance.md](references/style-and-governance.md)
  with [assets/spectral-openapi.yaml](assets/spectral-openapi.yaml) — only
  when setting up or extending Spectral linting of org conventions in CI,
  or choosing pagination/versioning strategy for a new API programme.
- [assets/template.openapi.yaml](assets/template.openapi.yaml) — a fuller
  lint-clean example (Location/201, 409 conflict, action sub-resource,
  reusable parameters) if the skeleton isn't enough.
- Authoritative spec: https://spec.openapis.org/oas/v3.1.1.html
