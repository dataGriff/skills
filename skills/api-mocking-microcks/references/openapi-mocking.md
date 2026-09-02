# OpenAPI mocking conventions

How to author (or retrofit) an OpenAPI 3.x spec so Microcks produces useful
REST mocks. Microcks supports OpenAPI 3.0/3.1 in YAML or JSON; Swagger 2.0
imports for documentation but needs a Postman collection or APIExamples
overlay to supply examples.

## Naming and identity

Microcks registers the API as `info.title` : `info.version`. Both are
mandatory. The mock base URL becomes:

```
http://<microcks>/rest/<url-encoded info.title>/<info.version>
```

Keep the title stable; bump the version to publish a parallel mock of a new
contract version.

## Named examples are the mock data

Use the **plural `examples`** keyword (a map of named examples), not the
singular `example` — names are how Microcks links a request to its response.
Every element of one logical exchange must share the same example name:
path/query parameters, request body, and response body.

```yaml
paths:
  /pastries/{name}:
    get:
      operationId: GetPastryByName
      parameters:
        - name: name
          in: path
          required: true
          schema: { type: string }
          examples:
            eclair:               # example name — the linking key
              value: Eclair
            donut:
              value: Donut
      responses:
        "200":
          content:
            application/json:
              examples:
                eclair:           # same name → paired with the request above
                  value: { name: Eclair, price: 2.5 }
                donut:
                  value: { name: Donut, price: 1.2 }
```

Now `GET /rest/API%20Pastries/1.0/pastries/Eclair` returns the eclair
payload and `/pastries/Donut` the donut one.

Rules that follow from this:

- Give **every required parameter** a value in each named example. A named
  example missing a required parameter cannot be matched.
- Response-only examples (a name that exists under `responses` but under no
  parameter/body) are only reachable via a custom dispatcher or as the only
  example of a parameter-less operation.
- Error cases are just more named examples on the error status code, with
  request examples that trigger them:

```yaml
      responses:
        "404":
          content:
            application/json:
              examples:
                unknown:
                  value: { error: "No such pastry" }
```

(with a matching `unknown: { value: NoSuchPastry }` under the path
parameter).

## Request bodies: `x-microcks-refs`

For POST/PUT operations Microcks matches on URL by default, so several body
examples under one URL need help. Either set a `JSON_BODY` dispatcher (see
dispatchers-and-templating.md) or annotate the request-body example with the
response example(s) it should map to:

```yaml
      requestBody:
        content:
          application/json:
            examples:
              launch_order:
                x-microcks-refs:
                  - created          # response example name(s) this body triggers
                value: { productId: 42, quantity: 2 }
```

## `x-microcks-operation`: delays and dispatchers in the spec

Attach mock behavior at the operation level so it travels with the spec:

```yaml
    post:
      operationId: CreateOrder
      x-microcks-operation:
        delay: 100                  # response latency in ms
        dispatcher: JSON_BODY
        dispatcherRules: |-
          {
            "exp": "/quantity",
            "operator": "range",
            "cases": { "[1;10]": "created", "default": "rejected" }
          }
```

`x-microcks` at the `info` level can also set API-wide `labels`.

## Overlays: examples/metadata without touching the spec

When the spec is generated or owned by another team, import it untouched as
the main artifact and layer Microcks-specific content as **secondary
artifacts** (upload with `mainArtifact=false`; metadata `name`/`version`
must match `info.title`/`info.version` exactly):

**APIExamples** — add or override mock exchanges:

```yaml
apiVersion: mocks.microcks.io/v1alpha1
kind: APIExamples
metadata:
  name: API Pastries
  version: "1.0"
operations:
  GET /pastries/{name}:
    millefeuille:
      request:
        parameters:
          name: Millefeuille
      response:
        status: "200"
        mediaType: application/json
        payload: { name: Millefeuille, price: 4.4 }
```

**APIMetadata** — set labels, delays, dispatchers per operation:

```yaml
apiVersion: mocks.microcks.io/v1alpha1
kind: APIMetadata
metadata:
  name: API Pastries
  version: "1.0"
  labels:
    domain: bakery
operations:
  GET /pastries:
    delay: 50
    dispatcher: URI_PARAMS
    dispatcherRules: size
```

A Postman collection with saved request/response examples works as a
secondary artifact too (same name:version in the collection description).

## Default dispatching (what Microcks infers)

With no explicit dispatcher, Microcks derives one from the operation shape:
path variables → `URI_PARTS`, query parameters → `URI_PARAMS`, both →
`URI_ELEMENT`. GETs with distinct parameter examples usually "just work";
reach for explicit dispatchers when bodies, headers, or defaults matter.

## Checklist before importing

- `info.title` and `info.version` present and final.
- Every operation has ≥1 named example; every required parameter has a value
  in each named example; request and response names line up.
- Bodies that select responses carry `x-microcks-refs` or the operation has
  a body-aware dispatcher.
- Spec passes an OpenAPI linter (spectral etc.). The
  [microcks-spectral-ruleset](https://github.com/microcks/microcks-spectral-ruleset)
  lints these mockability conventions directly — use it when available.
