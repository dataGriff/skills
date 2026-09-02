# OWASP API Security Top 10 (2023) — review reference

Per category: what it is, how to detect it in code or a spec, an exploit
sketch, and the fix. Categories are numbered as OWASP numbers them
(API1–API10); severity still comes from impact, not from the number.

## API1 — Broken Object Level Authorization (BOLA)

The caller is authenticated but the object they name isn't checked
against them. The most common and most exploited API flaw.

**Detect.** Any handler that takes an object ID (path/query/body) and
fetches or mutates by that ID alone. Grep for `find_by_id`, `get(id)`,
`findOne({_id: ...})`, `WHERE id = ?` in handlers behind auth middleware
and ask: where does the owner/tenant constraint enter? Also check
"indirect" IDs: foreign keys in request bodies (`accountId` on a
transfer), IDs inside signed URLs, and bulk endpoints taking ID arrays —
each element needs the check.

**Exploit.** Authenticated user A changes `/orders/17` to `/orders/18`
and reads B's order. With sequential IDs, a loop dumps the table.

**Fix.** Scope the query to the caller (`AND owner_id = :caller` /
tenant filter applied at the repository layer so handlers can't forget
it), or an explicit policy check before acting. Return the identical 404
for "missing" and "not yours". UUIDs mitigate enumeration but are not
authorization — the check is still required.

## API2 — Broken Authentication

Anything that lets an attacker become someone else: weak token
validation, credential stuffing, leaked secrets.

**Detect.** JWT decode calls with verification disabled
(`verify=False`, `{ algorithms: undefined }`, `jwt.decode` without
`jwt.verify` in JS libs); algorithm taken from the token header; shared
hardcoded secrets in the repo; login/password-reset endpoints with no
rate limit or lockout; tokens accepted from query strings; long or
absent expiry; password reset tokens that are guessable or don't expire.

**Exploit.** With `verify=False`, anyone forges a token claiming any
user id. With an `alg` downgrade (RS256 → HS256), the public key becomes
the HMAC secret and tokens are forgeable.

**Fix.** The full checklist lives in `authn.md` (same directory); the
non-negotiables: pin the algorithm list server-side, validate signature
+ `exp` + `iss` + `aud`, keys via JWKS by `kid`, rate-limit and lock out
on auth endpoints, hash stored credentials (bcrypt/argon2) and API keys.

## API3 — Broken Object Property Level Authorization (BOPLA)

Per-property authorization, in both directions: **mass assignment** on
write, **excessive exposure** on read.

**Detect.** Writes: request body bound straight into the model —
`Model(**request.json)`, `Object.assign(user, req.body)`, Rails
`update(params)` without strong parameters, Spring binding without
`@JsonIgnore`/DTOs. Reads: handlers serializing the ORM entity or the
raw document; list endpoints returning the same shape as admin views;
GraphQL resolvers exposing fields without per-field checks.

**Exploit.** `PATCH /users/me {"role": "admin"}` — the role field rides
into the update. Or `GET /users/42` returns `passwordHash`,
`isAdmin`, `stripeCustomerId` because the whole entity is serialized.

**Fix.** Explicit input DTO/allowlist per operation (create ≠ update);
reject unknown fields (`additionalProperties: false`, Pydantic
`extra="forbid"`). Explicit response models per audience; sensitive
fields opt-in, never opt-out.

## API4 — Unrestricted Resource Consumption

Nothing stops a caller from making the API do unbounded work — costing
availability or real money (SMS, email, LLM and other metered APIs).

**Detect.** No rate limiting on the route or gateway; list endpoints
where `limit`/`page_size` comes from the client without a server max;
unbounded arrays or string lengths in schemas; no request body size cap;
file uploads without size/type limits; endpoints that fan out to paid
third parties with no quota; missing timeouts on downstream calls;
zip/XML parsers without expansion limits.

**Exploit.** `?page_size=10000000`, a 2GB JSON body, or a loop on the
"send SMS code" endpoint that spends the Twilio budget overnight.

**Fix.** Server-side maximums on everything client-influenced (page
size, array items, body bytes, upload size), rate limits keyed per
principal (see `hardening.md` for design), timeouts + circuit breakers
downstream, spending quotas on metered operations.

## API5 — Broken Function Level Authorization (BFLA)

Whole endpoints or methods missing the role check — the admin function
next door to the user function.

**Detect.** Route table asymmetries: `/admin/*` or exports/reports
routed but not behind a role guard; handlers checking authentication
only where the UI hides the button; different HTTP methods on one path
with different guards (`GET` guarded, `DELETE` not); internal endpoints
"protected" only by obscurity or a shared header.

**Exploit.** A regular user calls `GET /admin/users/export` directly —
the UI never links it, the server never checks.

**Fix.** Role/permission check enforced in middleware *per route group*
plus deny-by-default routing: a new route gets no access until a policy
grants it. Verify method-level: guards must cover every verb on a path.

## API6 — Unrestricted Access to Sensitive Business Flows

The endpoint works as designed, but nothing stops abusive automation of
the flow: scalping checkouts, mass sign-ups, referral farming, scraping.

**Detect.** Business-critical flows (purchase, signup, vote, referral,
booking) with no per-human friction: no device/bot signal, no per-account
velocity caps, price/inventory endpoints pollable at machine speed.

**Fix.** Velocity limits per account/payment-instrument/device on the
flow (not just per-IP), step-up friction (CAPTCHA, verified contact) on
anomaly, and business-level detection (one card across many accounts).
This is a design conversation with the user — flag it rather than
inventing thresholds.

## API7 — Server-Side Request Forgery (SSRF)

The API fetches a URL the client influenced.

**Detect.** Any fetch/request call whose URL contains client input:
webhook registration + test/ping, URL imports ("fetch avatar from
URL"), PDF/preview generators, link unfurlers. Check redirects too — an
allowlisted host that 302s to `http://169.254.169.254/` defeats a naive
check.

**Exploit.** Register webhook `http://169.254.169.254/latest/meta-data/`
(cloud credentials) or `http://localhost:6379/` (internal Redis) and
read the response — or infer it from timing/errors in blind SSRF.

**Fix.** Scheme + host allowlist evaluated *after* DNS resolution;
block private, loopback, and link-local ranges; disable or re-validate
redirects; fetch from an egress-restricted network segment. Details in
`hardening.md`.

## API8 — Security Misconfiguration

The catch-all for deployment-layer gaps.

**Detect.** Missing TLS or TLS optional; CORS `*` (or origin echoed
back) combined with `Allow-Credentials: true`; stack traces / debug
pages in error responses; default credentials; directory listings;
verbose server banners; unnecessary HTTP methods enabled (TRACE);
missing security headers; cloud storage buckets public; outdated
dependency with known CVE doing the parsing.

**Exploit.** Echoed-origin CORS with credentials lets any website read
the victim's API responses in their browser. A stack trace hands over
paths, versions, and query shapes for free.

**Fix.** Header and CORS specifics in `hardening.md`. Treat config as
code: reviewed, versioned, identical shape across environments with
only values differing.

## API9 — Improper Inventory Management

You can't secure endpoints you forgot exist.

**Detect.** Diff the spec against the live route table — both
directions. Look for versioned paths (`/v1/` still routable after `/v2/`
shipped), `beta`/`internal`/`test` prefixes, mock or staging hosts
reachable from the internet with production data, undocumented debug
routes left by frameworks.

**Exploit.** `/v1/users/{id}` predates the BOLA fix that `/v2` got; the
old version still runs against the same database.

**Fix.** The spec is the inventory: generated from or verified against
routes in CI. Old versions get a retirement date and then actually
return 410. Non-production hosts don't hold production data.

## API10 — Unsafe Consumption of APIs

Trusting upstream APIs more than user input.

**Detect.** Third-party API responses used without validation: inserted
into queries, rendered into HTML, deserialized into rich objects,
followed as redirects; no timeout/size cap on upstream reads; webhook
receivers that skip signature verification (e.g. Stripe/GitHub HMAC) or
don't bound payloads.

**Exploit.** A compromised or spoofed partner sends a webhook whose
"order id" is an SQL injection payload; it's trusted because "it's from
the partner".

**Fix.** Validate upstream data against a schema exactly like client
input; verify webhook signatures (constant-time) before parsing the
body; timeouts and size caps on every upstream call; allowlist redirect
targets.

## Writing the findings report

Order: Critical → Low. Per finding:

```markdown
## [SEVERITY] Title naming the flaw and the asset
- **Category:** API1 BOLA (etc.)
- **Location:** `path/file.py:42` (or spec JSON pointer)
- **Exploit:** the concrete request an attacker sends and what they get
- **Fix:** the specific change — the check to add and where, the field
  to remove, the config value to set
```

Group systemic issues (same root cause across endpoints) into one
finding listing all locations. Close with what was *checked and found
sound* — an explicit "authentication middleware verifies signature,
expiry, issuer, audience" line tells the reader the silence elsewhere
was diligence, not omission.
