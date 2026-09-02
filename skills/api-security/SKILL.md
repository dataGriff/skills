---
name: api-security
description: >-
  Review, harden, and design HTTP APIs against the OWASP API Security Top 10
  (2023): object- and property-level authorization (BOLA/IDOR, mass
  assignment, over-exposure), authentication and JWT/OAuth2 token
  validation, unrestricted resource consumption and rate limiting, SSRF,
  misconfiguration (CORS, TLS, headers, error leakage), and endpoint
  inventory. Produces evidence-backed findings ranked by severity with
  concrete fixes. Use when the user asks for an API security review, audit,
  or threat model, asks "is my API secure" or to prepare for a pen test,
  mentions BOLA, IDOR, broken auth, mass assignment, rate limiting, or the
  OWASP API Top 10, wants security requirements for a new API design, or
  asks to fix an authentication or authorization bug in an API.
---

# API security

Two jobs share this skill: **reviewing** an existing API (implementation
code, an OpenAPI spec, or both) and **designing security into a new one**.
Both work from the same model of how APIs actually get broken — the OWASP
API Security Top 10 (2023) — but a review produces findings, and a design
produces requirements. Never produce a generic checklist dump: every
finding cites the file and line (or spec path) where it lives, and every
requirement is specific to the API's resources and callers.

## Review workflow

1. **Map the attack surface.** Enumerate every route from the router,
   controller annotations, or spec `paths`. For each, note: HTTP method,
   auth requirement (which middleware/decorator, or none), object IDs it
   accepts (path, query, or body), and whether it writes. Endpoints in
   code but missing from the spec (or vice versa) are themselves findings.
2. **Trace authentication once.** Follow the auth middleware end to end:
   how tokens are parsed, what is verified, where the secret/keys come
   from. One flaw here (signature not verified, `alg` not pinned,
   hardcoded secret) undermines everything downstream, so it outranks
   most per-endpoint issues. If token handling looks nonstandard, check
   it against [references/authn.md](references/authn.md).
3. **Interrogate each endpoint** with four questions, in this order:
   - *Who can call this?* (authentication — is it enforced, not just
     documented?)
   - *Can the caller touch this object?* (authorization — is the ID from
     the request checked against the caller's identity/tenant, in the
     handler or query?)
   - *Is every input bounded?* (schema-validated, length/size/range caps,
     unknown fields rejected on writes)
   - *Does the output leak?* (extra properties, other users' data in
     list endpoints, stack traces, secrets in errors or logs)
4. **Verify before reporting.** For each candidate finding, trace the
   actual code path and state the concrete exploit ("caller A requests
   `GET /orders/17` owned by B; the handler at `orders.py:42` fetches by
   id with no owner check"). Drop anything you cannot evidence — a
   security review that cries wolf gets ignored. Consult
   [references/top10.md](references/top10.md) if a category needs
   detection heuristics or you're unsure whether something qualifies.
5. **Rank and report.** Order findings by severity (below), formatted:

   ```markdown
   ## [SEVERITY] Title naming the flaw and the asset
   - **Category:** API1 BOLA (the OWASP API Top 10 category)
   - **Location:** `path/file.py:42` (or spec JSON pointer)
   - **Exploit:** the concrete request an attacker sends, and what they get
   - **Fix:** the specific change — which check, added where
   ```

   One systemic cause (e.g. "no handler checks object ownership") is one
   finding listing every affected endpoint, not ten copies. Close the
   report with what was checked and found sound — an explicit "token
   validation verifies signature, expiry, issuer, audience" line tells
   the reader the silence elsewhere was diligence, not omission. Fix the
   code only when the user asked for fixes, not just a review.

## Severity

Rank by what an attacker gets, not by how untidy the code is:

- **Critical** — pre-auth compromise or cross-tenant data access at scale:
  unauthenticated access to sensitive data, signature-unverified tokens,
  BOLA on bulk/list endpoints, injection reaching the data store.
- **High** — authenticated but unauthorized access: BOLA on single
  objects, privilege escalation via mass assignment (e.g. a writable
  `role`), SSRF reaching internal networks, secrets in the repo.
- **Medium** — meaningful weakening: missing rate limits on auth or
  costly endpoints, unbounded pagination/payloads, permissive CORS with
  credentials, verbose errors leaking internals.
- **Low** — defense-in-depth gaps: missing headers, sloppy logging,
  deprecated-but-harmless endpoints still routable.

One systemic cause (e.g. "no handler checks object ownership") is one
finding with all affected endpoints listed, not ten copies.

## The rules that decide most findings

- **Authorization lives in the handler, per object.** Middleware proves
  *who* is calling; it cannot know *what* they may touch. Every handler
  that resolves a client-supplied ID must check that object against the
  caller — by scoping the query (`WHERE id = ? AND owner_id = ?` or the
  tenant filter) or an explicit ownership/role check before acting. A
  handler that fetches by bare ID is BOLA — the most exploited API flaw —
  regardless of how good the authentication is. Return the same 404 for
  "doesn't exist" and "not yours", or object IDs become enumerable.
- **Authorization is also per property.** Writes bind an explicit
  allowlist of fields (a create/update DTO), never the raw body into the
  model — otherwise `{"role": "admin"}` rides along (mass assignment).
  Reads serialize an explicit response model, never the ORM object —
  otherwise password hashes and internal flags ride out.
- **Verify tokens like they're forged.** Decode-without-verify is a
  Critical finding, always. Minimum: signature checked against a pinned
  algorithm allowlist (never the token's own `alg` header, never `none`),
  `exp`, `iss`, and `aud` all validated, keys fetched by `kid` from the
  issuer's JWKS (not a hardcoded secret for RS256). API keys are hashed
  at rest and compared constant-time. Details, including OAuth2 flow
  choice and common JWT pitfalls, when needed:
  [references/authn.md](references/authn.md).
- **Bound every input.** Validate against a schema at the boundary;
  reject unknown fields on writes; cap string lengths, array sizes,
  page sizes (`limit` ≤ a server max), and request body size; enforce
  content-type. Anything unbounded is a resource-consumption attack —
  against your infrastructure or your per-call-priced dependencies.
- **Treat client-supplied URLs as hostile** (webhooks, imports, avatars):
  allowlist schemes and hosts, resolve and block private/link-local
  ranges (169.254.169.254 is the classic target), don't follow redirects
  into them. Otherwise the API is an SSRF proxy into your network.
- **Fail closed and fail quiet.** Unhandled errors return a generic
  problem response, never stack traces, queries, or dependency versions.
  Secrets never appear in URLs (they end up in logs and referrers) nor
  in log lines. Authorization denials are logged (they're your intrusion
  signal); credentials and tokens are not.
- **Configuration is attack surface.** TLS-only with HSTS; CORS
  allowlists specific origins (never `*` together with credentials);
  debug endpoints, default credentials, and stack-trace pages are off in
  production. Platform-level hardening patterns — rate-limit design,
  headers, egress controls — when you're configuring rather than
  reviewing: [references/hardening.md](references/hardening.md).

## Designing a new API

State security requirements as concretely as endpoints. Secure defaults
that cost little at design time and a rewrite later:

- Deny by default: a global security requirement in the spec, with
  `security: []` only on deliberately public operations. (Declaring
  schemes in OpenAPI is the openapi-authoring skill's territory; this
  skill decides *what* to require.)
- Scopes/permissions named `resource:verb`, mapped per operation, checked
  server-side — the token's scopes bound what the handler will do.
- Every collection endpoint paginated with a server-enforced max page
  size; every mutation idempotent or idempotency-keyed.
- 429 with `Retry-After` on rate limits, RFC 9457 problem responses for
  errors, and both documented in the spec so clients handle them.
- An explicit data classification: which fields are sensitive, which
  endpoints return them, and the extra controls (scopes, audit logging)
  those endpoints carry.

## When to open the references

- [references/top10.md](references/top10.md) — the OWASP API Top 10
  (2023) category by category: detection heuristics, exploit examples,
  fixes. Open when writing up findings, or when deciding whether an
  observation qualifies and under which category.
- [references/authn.md](references/authn.md) — token validation in
  depth: JWT pitfalls, JWKS rotation, OAuth2 flow selection, API keys,
  session cookies, login hardening. Open when reviewing or implementing
  authentication.
- [references/hardening.md](references/hardening.md) — rate limiting
  design, CORS, security headers for APIs, TLS, SSRF egress controls,
  secrets handling, logging. Open when configuring platform protections
  or fixing a Medium/Low misconfiguration finding.
