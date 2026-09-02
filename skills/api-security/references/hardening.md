# Platform hardening for APIs — configuration reference

Deployment-layer protections: rate limiting, CORS, headers, TLS, SSRF
egress, secrets, logging. Open this when configuring or when fixing a
misconfiguration finding; the review heuristics live in `top10.md`.

## Rate limiting

Design decisions, in order:

- **Key** by authenticated principal (user/client id) first, IP only as
  the pre-auth fallback — per-IP alone is defeated by botnets and
  punishes NATed offices. Sensitive flows also key by resource
  (per-account login attempts, per-card checkout).
- **Tiers**: a global backstop per principal, tighter budgets on
  expensive or abusable routes (auth, search, export, send-message,
  anything calling a metered third party).
- **Algorithm**: token bucket (or sliding window) for burst tolerance;
  fixed windows allow 2× bursts at the boundary. Enforce at the gateway
  where possible so it can't be skipped, backed by a shared store
  (e.g. Redis) when the API has replicas.
- **Response**: `429` with `Retry-After`, plus `RateLimit-*` (or
  `X-RateLimit-*`) headers on successful responses so well-behaved
  clients can pace. Document both in the spec.
- Rate limiting caps *velocity*; size caps (body bytes, page size,
  upload size, array lengths) cap *work per request*. Both are needed.

## CORS

CORS controls which *browser origins* may read responses — it is not
authentication and does not restrict curl or servers.

- Allowlist exact origins. Never combine
  `Access-Control-Allow-Origin: *` — nor its moral equivalent, echoing
  the request's `Origin` back — with `Access-Control-Allow-Credentials:
  true`; that grants every website on earth the user's authenticated
  session.
- A public, unauthenticated read-only API can use `*` (without
  credentials) legitimately.
- Keep allowed methods/headers minimal; cache preflights with
  `Access-Control-Max-Age`.
- Regex origin checks are a classic hole: `example.com$` matches
  `evil-example.com`; unescaped dots match anything. Compare exact
  strings against a list.

## Security headers (JSON APIs)

- `Strict-Transport-Security: max-age=31536000; includeSubDomains` —
  after confirming all subdomains serve TLS.
- `X-Content-Type-Options: nosniff` and accurate `Content-Type` on
  every response (`application/json`, `application/problem+json`).
- `Cache-Control: no-store` on responses carrying personal or
  authenticated data — shared caches and browser history are leak paths.
- `Content-Security-Policy: default-src 'none'` and
  `X-Frame-Options: DENY` cost nothing and neutralize an API response
  rendered as a page.
- Strip `Server`/`X-Powered-By` version banners.

## TLS

TLS 1.2 minimum (1.3 preferred), certificates from a real CA and
auto-renewed. HTTP either refuses connections or 301s to HTTPS with
HSTS — but never *serves the API* over HTTP. Internal hops are not
exempt by being internal; terminate at the edge only when the network
behind it is genuinely isolated, otherwise mTLS or a service mesh.
Client code disabling verification (`verify=False`,
`rejectUnauthorized: false`, `InsecureSkipVerify`) is a finding wherever
it appears, tests included — it metastasizes.

## SSRF egress controls

Application-level checks (from SKILL.md: scheme+host allowlist after
DNS resolution, private/link-local ranges blocked, redirects
re-validated) plus platform backstops:

- Run URL-fetching features from an egress-restricted segment: deny
  RFC 1918, loopback, and 169.254.0.0/16 outbound; allowlist known
  destinations where feasible.
- Cloud metadata: require IMDSv2 (session tokens) on AWS or the
  equivalent hardening elsewhere, so a bare GET can't read credentials.
- Beware DNS rebinding: resolve once, validate the IP, connect to that
  IP (pinning), rather than validating and re-resolving.

## Secrets

- No secrets in code, config files in the repo, or container images —
  including "just for tests". Inject at runtime from a secrets manager
  or environment; a secret found in git history is compromised: rotate
  it, don't just delete the file.
- Secret scanning (gitleaks, trufflehog, GitHub push protection) in CI.
- Distinct credentials per environment; production secrets unreadable
  from staging. Database credentials per service with least privilege —
  the API's DB user needs no DDL and no access to other services'
  schemas.

## Logging and monitoring

- Log every authentication decision and every authorization *denial*
  with principal, route, and object id — denials are the intrusion
  signal (a BOLA sweep looks like hundreds of 404s from one principal).
- Never log credentials, tokens, session ids, or full sensitive
  payloads; scrub `Authorization` and cookie headers at the logging
  layer, not per call site.
- Log as structured data with a request id propagated end to end.
- Log injection: strip CR/LF from user-controlled values interpolated
  into text logs.
- Alert on: auth-failure spikes per principal/IP, 403/404 sweeps,
  rate-limit saturation, and traffic to deprecated endpoints
  (inventory drift — see `top10.md` API9).
