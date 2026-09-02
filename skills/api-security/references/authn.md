# Authentication for APIs — validation reference

How to validate credentials correctly, and the specific mistakes that
turn "we use JWTs" into "anyone can be anyone".

## JWT validation checklist

Every bearer-token API must do all of these on every request:

1. **Pin the algorithm server-side.** Pass an explicit allowlist
   (`algorithms=["RS256"]`) to the verify call. Never derive it from the
   token's own `alg` header: `none` disables verification entirely, and
   an RS256→HS256 downgrade turns the *public* key into an HMAC secret,
   making tokens forgeable by anyone who has it (everyone).
2. **Verify the signature** — a library call that *decodes* without
   *verifying* is the classic bug: PyJWT's
   `jwt.decode(t, options={"verify_signature": False})`, jsonwebtoken's
   `jwt.decode()` (vs `jwt.verify()`), java-jwt's `JWT.decode()` (vs
   building a `JWTVerifier`). Treat any of these on a request path as a
   Critical finding.
3. **Validate the standard claims**: `exp` (with small leeway, ≤ ~60s),
   `nbf` if present, `iss` equals the expected issuer exactly, and `aud`
   contains *this* API's identifier. Skipping `aud` means a token minted
   for any other service at the same issuer works here — a common
   real-world escalation.
4. **Resolve keys via JWKS**: fetch the issuer's
   `/.well-known/jwks.json`, select by the token's `kid`, cache with a
   TTL, and refresh on unknown `kid` (that's how rotation works —
   rate-limit the refresh so bogus `kid`s can't hammer it). Hardcoded
   verification keys break on rotation and end up in repos.
5. **Then authorize.** A valid token proves identity; scopes/roles in
   claims still need checking against the operation, and object access
   against the caller (BOLA — see SKILL.md).

Access tokens are short-lived (minutes to an hour); long expiry is a
finding because revocation is otherwise fiction. Refresh tokens stay
server-side or in an HttpOnly cookie, never in JS-readable storage, and
rotate on use. Don't put secrets or PII in JWT payloads — they're only
base64, readable by anyone who holds the token.

## OAuth2 / OIDC flow selection

- **Authorization code + PKCE** — anything with a user: web apps, SPAs,
  mobile. PKCE is mandatory practice for public clients and harmless for
  confidential ones.
- **Client credentials** — service-to-service, no user involved.
- **Implicit** and **resource owner password** — deprecated (OAuth 2.1
  removes them); their presence in new designs or configs is a finding.

Validate `redirect_uri` by exact match against registration — prefix or
substring matching enables token theft via open-redirect chaining. The
`state` parameter (or PKCE) must be checked on the callback or the flow
is CSRF-able.

## API keys

Fine for identifying server-side callers; not an authorization system
and not for browsers (they leak in bundles and DevTools).

- Generate ≥128 bits of CSPRNG randomness; give keys a recognizable
  prefix (`sk_live_...`) so secret scanners can catch leaks.
- Store only a hash (SHA-256 is fine — keys are high-entropy, unlike
  passwords); look up by key-id prefix, compare digests constant-time
  (`hmac.compare_digest`, `crypto.timingSafeEqual`). A `==` on secrets
  is a timing oracle.
- Accept keys in a header (`Authorization` or `X-Api-Key`), never in
  query strings — URLs persist in access logs, proxies, and referrers.
- Support multiple active keys per client and record last-used, so
  rotation and revocation are operationally possible.

## Session cookies

If the API authenticates browsers by cookie: `Secure`, `HttpOnly`,
`SameSite=Lax` (or `Strict`); session ID is random and regenerated at
login (fixation); server-side revocation on logout. `SameSite=None`
means CSRF defenses (origin check or tokens) are back on the table for
state-changing endpoints.

## Login and recovery hardening

- Rate-limit and lock out (or exponentially back off) per account *and*
  per IP on login, token, and password-reset endpoints — they are the
  credential-stuffing surface.
- One generic failure message; identical timing for "no such user" and
  "wrong password" as far as practical.
- Password reset tokens: single-use, short-lived, CSPRNG, stored hashed;
  the reset flow never confirms account existence.
- Hash passwords with argon2id or bcrypt; a fast hash (SHA-family,
  MD5) for passwords is a High finding even salted.
- MFA where the data warrants it; recovery paths must not be the weak
  bypass (SMS-reset undoing TOTP).
