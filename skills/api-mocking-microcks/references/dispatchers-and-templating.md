# Dispatchers and response templating

Two mechanisms make Microcks mocks smart: **dispatchers** choose *which*
example answers a request; **templates** make the chosen response *dynamic*.

## Dispatchers

A dispatcher + dispatcher rules live on an operation (set via
`x-microcks-operation` in the spec, an APIMetadata overlay, or the UI's
operation properties — spec/overlay wins on re-import). The dispatcher
computes a *dispatch criteria* string from the incoming request; the
example whose own criteria matches is returned.

| Dispatcher | Matches on | Rules syntax |
| --- | --- | --- |
| `URI_PARTS` | path variable values | variable names, e.g. `name` or `id && subid` |
| `URI_PARAMS` | query parameter values | param names, e.g. `page && limit` |
| `URI_ELEMENT` | both of the above | `id ?? page && limit` (parts `??` params) |
| `QUERY_HEADER` | header values | header names, e.g. `x-tenant` |
| `JSON_BODY` | request body content | JSON config, below |
| `SCRIPT` | anything (Groovy) | script returning an example name |
| `FALLBACK` | delegate + default | JSON config, below |
| `PROXY` | nothing — forwards | base URL of the real backend |
| `PROXY_FALLBACK` | delegate, else forward | JSON config with `proxyUrl` |
| `RANDOM` | nothing — picks randomly | — |

Defaults are inferred from the operation (path vars → `URI_PARTS`, etc.),
so explicit dispatchers are mostly needed for bodies, headers, fallbacks,
and logic.

### JSON_BODY

Rules are a JSON object: `exp` is a JSON-pointer into the request body,
`operator` one of `equals`, `range`, `size`, `regexp`, `presence`, and
`cases` maps values to **response example names** (`default` is the
catch-all):

```json
{
  "exp": "/country",
  "operator": "equals",
  "cases": { "US": "us_pricing", "FR": "eu_pricing", "default": "intl_pricing" }
}
```

Range example: `"operator": "range"`, cases keyed like `"[1;10]"`
(inclusive brackets, `]1;10[` exclusive). `size` works on array length,
`presence` has cases `found`/`default`.

Two mistakes silently break JSON_BODY dispatching: omitting the
`"operator"` field, and prefixing case keys (`"range(1,10)"`,
`"range[1;10]"`) — keys are bare `[..;..]` intervals, nothing else. Case
*values* must be response example names that exist, or matches 400.

### SCRIPT

A Groovy script with `mockRequest` in scope; return the example name.
Useful for header+body combos or pseudo-state:

```groovy
def json = new groovy.json.JsonSlurper().parseText(mockRequest.requestContent)
if (json.quantity > 100) return "rejected"
return mockRequest.getRequestHeaders().get("x-beta", "none") == "true" ? "beta" : "created"
```

Scripts can also read `store` (a per-instance key/value store) for simple
stateful scenarios, and `requestContext` to pass values into response
templates.

### FALLBACK

Wraps another dispatcher and names the example to serve when nothing
matches — the fix for "unmatched requests should get a sensible default,
not a 400":

```json
{ "dispatcher": "URI_PARTS", "dispatcherRules": "name", "fallback": "donut" }
```

`PROXY_FALLBACK` is the same shape with `"proxyUrl"` instead of
`"fallback"`: unmatched requests hit the real backend — handy for mocking
only new/unbuilt operations of an existing API.

## Response templating

Anywhere in an example payload or header value, `{{ }}` expressions render
at serve time. Works for REST responses and async event payloads alike.

**Request-derived values:**

```
{{ request.body }}                 whole request body
{{ request.body/items/0/sku }}     JSON pointer into the body
{{ request.path[1] }}              path segment by index
{{ request.params[page] }}         query parameter
{{ request.headers[x-request-id] }}
```

**Generators:**

```
{{ guid() }}            {{ now() }}              {{ now(dd/MM/yyyy HH:mm:ss) }}
{{ randomInt() }}       {{ randomInt(5, 50) }}   {{ randomString(24) }}
{{ randomBoolean() }}   {{ randomValue(a,b,c) }} {{ uuid() }} {{ randomUUID() }}
{{ randomFirstName() }} {{ randomLastName() }}   {{ randomFullName() }}
{{ randomEmail() }}     {{ randomCity() }}       {{ randomStreetAddress() }}
```

**Context:** `{{ requestContext.foo }}` reads values a SCRIPT dispatcher
stored via `requestContext.foo = ...` — the way to compute once and use in
both dispatch and response.

Echo-style creation mock:

```yaml
              examples:
                created:
                  value:
                    id: "{{ guid() }}"
                    createdAt: "{{ now(yyyy-MM-dd'T'HH:mm:ssZ) }}"
                    productId: "{{ request.body/productId }}"
                    quantity: "{{ request.body/quantity }}"
                    status: pending
```

Notes:

- Quote templated scalars in YAML — `{{` starts a YAML flow mapping
  otherwise.
- A template that fails to evaluate renders as the literal `{{ ... }}`
  text in the response; treat that in output as a bug in the expression
  (typo'd function or bad pointer), not as Microcks being down.
- Templating happens after example selection: templates cannot influence
  which example is chosen — that is the dispatcher's job.
