# Security schemes and requirements

Authentication is declared in two halves: **schemes** (how a credential is
presented) under `components/securitySchemes`, and **requirements** (which
schemes an operation needs) in `security` at the root or on an operation.
A spec with neither documents an API nobody can call correctly.

## Scheme types

```yaml
components:
  securitySchemes:
    bearerAuth:                 # key = the name requirements refer to
      type: http
      scheme: bearer
      bearerFormat: JWT         # documentation hint only
    basicAuth:
      type: http
      scheme: basic
    apiKey:
      type: apiKey
      name: X-Api-Key           # header/query/cookie parameter name
      in: header                # header | query | cookie (avoid query — logged in URLs)
    oauth:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          refreshUrl: https://auth.example.com/token
          scopes:
            orders:read: Read orders
            orders:write: Create and modify orders
        clientCredentials:
          tokenUrl: https://auth.example.com/token
          scopes:
            orders:read: Read orders
    oidc:
      type: openIdConnect
      openIdConnectUrl: https://auth.example.com/.well-known/openid-configuration
    mtls:
      type: mutualTLS           # new in 3.1; no further fields
```

Choose flows to match real clients: `authorizationCode` (with PKCE) for
user-facing apps, `clientCredentials` for service-to-service. `implicit`
and `password` are deprecated by OAuth 2.1 practice — don't add them to new
specs. Scope names and descriptions are contract surface: name them
`resource:verb` and describe what each grants.

Never put example tokens, real keys, or credential values anywhere in a
spec — scheme objects describe the mechanism only.

## Applying requirements

```yaml
security:                    # root level: the default for every operation
  - bearerAuth: []           # non-OAuth schemes always take an empty array
paths:
  /orders:
    post:
      security:              # override: this op needs a scope
        - oauth: [orders:write]
  /health:
    get:
      security: []           # explicitly public — an empty requirement list
```

Semantics of the `security` array:

- **List entries are OR** — the caller satisfies *any one* entry.
- **Keys within one entry are AND** — `- apiKey: []` + `bearerAuth: []` in
  the same mapping means both at once.
- The array value carries **scopes** for `oauth2`/`openIdConnect` schemes
  and must be `[]` for every other type.
- An operation-level `security` **replaces** the root default entirely (no
  merging); `security: []` removes auth — use it deliberately and only for
  genuinely public endpoints (health, discovery).

Set a root-level default so new operations are secure by omission, then
override per operation for scopes and public endpoints. Document `401` and
`403` responses on secured operations (via shared component responses) —
they're part of the contract callers must handle.
