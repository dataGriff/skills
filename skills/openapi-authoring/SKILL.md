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

Write API descriptions against **OpenAPI 3.1** (`openapi: 3.1.0`), the
OpenAPI Initiative standard whose schemas are full JSON Schema 2020-12. One
YAML document, conventionally named `openapi.yaml` (or `<api>.openapi.yaml`
when a repo holds several). OpenAPI 3.2 exists (released 2025) but tooling
support lags; default to 3.1 unless the user's toolchain is confirmed on
3.2, and never start a new spec on 3.0 or Swagger 2.0.

Start from [assets/template.openapi.yaml](assets/template.openapi.yaml) —
copy it and adapt, rather than writing from a blank page. Lint the result
with `spectral lint <file>` if Spectral is available (its built-in
`spectral:oas` ruleset also catches structural errors); `redocly lint` is an
equivalent alternative.

## The shape of a document

```yaml
openapi: 3.1.0            # spec version — 3.1.x for new documents
info:                     # required: title + version, plus real description
  title: Orders API
  version: 1.2.0          # the API's version (semver), not the spec's
  description: ...
servers: [...]            # base URLs per environment
tags: [...]               # operation grouping, drives docs navigation
security: [...]           # default auth applied to every operation
paths:                    # the API surface: one path item per URL template
  /orders:
    get: {...}            # operation objects: summary, params, responses
    post: {...}
webhooks: {...}           # out-of-band calls the API makes to consumers
components:               # every reusable piece lives here, used via $ref
  schemas: {...}
  parameters: {...}
  responses: {...}
  securitySchemes: {...}
```

Only `openapi`, `info`, and one of `paths`/`components`/`webhooks` are
required — but a spec that stops there documents nothing. A useful spec
describes every response a client can receive (errors included), models
request/response bodies as named component schemas, and declares how callers
authenticate.

## Workflow

1. **Model resources before routes.** Identify the nouns (order, customer),
   their lifecycle (create/read/list/update/delete/transitions), who calls
   them and how they authenticate. Routes, schemas, and security fall out of
   this; URLs invented first tend to become verbs.
2. **Write fundamentals** — info (title, semver version, description of what
   the API is for and who it serves), servers per environment, tags with
   descriptions.
3. **Declare paths and operations.** One path item per URL template, plural
   kebab-case resource names, no verbs in paths. Every operation gets a
   unique camelCase `operationId` (it becomes function names in generated
   clients), a summary, tags, and a complete `responses` map — success
   codes, expected 4xx, and a default error. Read
   [references/structure.md](references/structure.md) for path items,
   operations, parameters, request bodies, responses, and webhooks.
4. **Model schemas in components.** Define every non-trivial body as a named
   schema under `components/schemas` and reference it with `$ref` — inline
   schemas can't be reused or targeted by codegen. Use JSON Schema 2020-12
   idioms: `type: [string, "null"]` for nullable, `examples`, composition
   via `allOf`/`oneOf` with `discriminator`. Read
   [references/schemas-and-components.md](references/schemas-and-components.md)
   for the full field set, composition patterns, and 3.0→3.1 migration.
5. **Declare security.** Define schemes in `components/securitySchemes`,
   apply a global default in top-level `security`, override per operation
   (`security: []` for the rare public endpoint). Read
   [references/security.md](references/security.md) for scheme types, OAuth2
   flows, scopes, and patterns.
6. **Add examples where behaviour isn't obvious** — request/response pairs
   for tricky operations, one per `oneOf` branch. Examples are executable
   documentation; mock servers and doc renderers surface them directly.
7. **Validate.** `spectral lint <file>` (structural + `spectral:oas` best
   practices). Fix errors top-to-bottom; warnings are usually worth fixing
   too.
8. **Enforce conventions with Spectral.** Schema validation accepts
   `/getOrders` and a missing error response; org style rules (casing,
   required descriptions, problem+json errors, pagination) need a custom
   ruleset — start from
   [assets/spectral-openapi.yaml](assets/spectral-openapi.yaml) and run it
   in CI. Read
   [references/style-and-governance.md](references/style-and-governance.md)
   for naming conventions, error and pagination patterns, versioning, and
   writing new rules.

## Authoring judgment

- **`info.version` is the API's version, not the spec's.** Bump it semver:
  major for breaking changes (removed/renamed field or operation, tightened
  validation, new required parameter), minor for additive. `openapi: 3.1.0`
  only changes when adopting a newer standard.
- **The spec is the contract, not a code dump.** Describe what a client can
  rely on — don't mirror internal DB columns or leak implementation names.
  If generated from code annotations, review the output against these rules
  as if hand-written.
- **Every response a client can see, documented.** At minimum: the success
  code with its schema, 400/401/403/404/409/422 where they apply, and a
  `default` error response. An undocumented 500 shape is where every client
  integration breaks.
- **Errors are one shared model.** Use RFC 9457 `application/problem+json`
  (or the org's established shape) as a single `components` schema +
  response, referenced everywhere — not per-endpoint ad-hoc error bodies.
- **Prefer `$ref` over repetition.** Repeated parameters (pagination, ids),
  headers, and responses belong in `components`; drift between inline
  copies is a bug factory.
- **Additive by default.** Design so growth is non-breaking: optional new
  fields, new enum values only where clients are told to tolerate unknowns,
  no repurposing of existing fields.

## References

- [references/structure.md](references/structure.md) — root object, info,
  servers, tags, path items, operations, parameters, request bodies,
  responses, headers, links, and webhooks.
- [references/schemas-and-components.md](references/schemas-and-components.md)
  — components sections, JSON Schema 2020-12 fields, nullability,
  composition and discriminators, examples, binary payloads, and 3.0→3.1
  migration.
- [references/security.md](references/security.md) — security scheme types,
  OAuth2 flows and scopes, applying and overriding security requirements.
- [references/style-and-governance.md](references/style-and-governance.md) —
  naming conventions, error model, pagination, API versioning, and
  enforcing org rules with a Spectral ruleset (starter ruleset in assets/,
  custom rule patterns, CI wiring).
- [assets/template.openapi.yaml](assets/template.openapi.yaml) — a complete,
  lint-clean starter spec to copy.
- Authoritative spec: https://spec.openapis.org/oas/v3.1.1.html — consult it
  for anything not covered here.
