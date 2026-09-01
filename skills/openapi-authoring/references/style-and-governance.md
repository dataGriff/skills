# Style conventions and governance

Schema-valid is not the same as well-designed: the validator happily accepts
`/getOrders`, a POST with no error responses, and five different error
bodies. These conventions (and the Spectral ruleset that enforces them) are
the difference.

## Naming conventions

- **Paths**: plural kebab-case resource nouns, no verbs, no trailing slash,
  no file extensions — `/purchase-orders/{orderId}/line-items`. Nest at most
  one level of ownership; deeper hierarchies become unusable filters.
  Non-CRUD actions get a verb *sub-resource* on the parent:
  `POST /orders/{orderId}/cancel`.
- **Path parameters**: camelCase, prefixed with the resource for clarity in
  generated clients (`orderId`, not `id`).
- **Query parameters**: camelCase (`pageSize`, `sortBy`); pick one casing
  org-wide and lint for it.
- **Properties**: camelCase for JSON bodies (or snake_case if the org
  already ships it — consistency beats preference; encode the choice in the
  ruleset).
- **operationId**: camelCase verb + resource — `listOrders`, `getOrder`,
  `createOrder`, `cancelOrder`. Unique across the document.
- **Schema names**: UpperCamelCase (`Order`, `OrderCreate`, `Problem`).
- **Enum values**: pick one style (lower-case or SCREAMING_SNAKE) and keep
  it; enum churn is a breaking change, so document whether clients must
  tolerate unknown values.

## Error model

Use RFC 9457 (Problem Details, `application/problem+json`) unless the org
has an established shape. One schema + shared component responses,
referenced from every operation:

```yaml
components:
  schemas:
    Problem:
      type: object
      properties:
        type: {type: string, format: uri, default: "about:blank"}
        title: {type: string}
        status: {type: integer}
        detail: {type: string}
        instance: {type: string, format: uri}
  responses:
    NotFound:
      description: The resource does not exist.
      content:
        application/problem+json:
          schema: {$ref: "#/components/schemas/Problem"}
```

Every operation ends its responses map with
`default: {$ref: "#/components/responses/Error"}` so undeclared statuses
still have a documented shape. Extend `Problem` (extra fields are allowed
by the RFC) rather than inventing parallel error bodies.

## Pagination

Standardise one mechanism and reuse its parameters from `components`.
Cursor-based scales best: `pageSize` + `pageToken` in, items plus
`nextPageToken` out (absent/null token = last page). Offset/limit is fine
for small, stable collections. Either way the list response is an object
wrapping the array — never a bare top-level array, which can't grow
metadata without breaking clients.

## API versioning

- Major version in the **server URL** (`https://api.example.com/v1`), not in
  every path and not in a query parameter. Header-based versioning is
  defensible but harder to route and document — don't mix strategies.
- `info.version` tracks the document/API semver independently of the URL
  major (`/v1` + `info.version: 1.4.0`).
- Within a major: additive changes only. Removing/renaming fields or
  operations, tightening validation, adding required parameters, or
  changing auth all mean `/v2`. Mark retiring operations
  `deprecated: true` and say what replaces them in the description before
  ever removing them.

## Enforcing with Spectral

Spectral's built-in `spectral:oas` ruleset covers structural best practice
(operationIds, descriptions, unused components, example validity). Org
conventions go in a custom ruleset extending it — starter:
[../assets/spectral-openapi.yaml](../assets/spectral-openapi.yaml).

```bash
npm install -g @stoplight/spectral-cli
spectral lint --ruleset spectral-openapi.yaml openapi.yaml
```

Anatomy of a custom rule:

```yaml
rules:
  paths-kebab-case:
    description: Path segments must be kebab-case.
    severity: error
    given: $.paths[*]~                # JSONPath; ~ selects the key itself
    then:
      function: pattern
      functionOptions:
        match: "^(/[a-z0-9-]+|/\\{[a-zA-Z0-9]+\\})+$"
```

`given` selects nodes (`~` targets keys), `then` applies a function:
`pattern`, `truthy`, `defined`, `enumeration`, `length`, `schema`, or
`casing`. Set real severities — `error` fails CI, `warn` nags. Suppress a
justified exception inline with an override block in the ruleset, not by
downgrading the rule globally.

In CI, lint every spec change (`spectral lint --fail-severity=error`) and
optionally diff for breaking changes (`oasdiff breaking old.yaml new.yaml`
or `redocly diff`) so a major-version bump can't slip through as a patch.
