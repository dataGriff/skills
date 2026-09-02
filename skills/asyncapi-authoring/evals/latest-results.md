# Eval results: asyncapi-authoring

Last run: 2026-09-01 UTC, iterations 20260901-2200-r1/r2/r3 — 3 runs per
arm per eval, run via session subagents; rerun with
`task eval:skills NAME=asyncapi-authoring` (single iteration). Commit this
file with the skill change so the PR carries the evidence. Both arms had
the AsyncAPI CLI and Spectral on PATH; the grader also scores authoring
outputs against the skill's Spectral governance ruleset.

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| author-inventory-asyncapi | 24/24 | 23/24 | 43.5s / 44.7s | 51.9k tok / 41.5k tok |
| review-legacy-asyncapi | 21/21 | 21/21 | 92.7s / 93.7s | 63.5k tok / 46.8k tok |
| author-request-reply-avro | 24/24 | 24/24 | 53.2s / 102.8s | 58.6k tok / 44.2k tok |

Scores sum 3 runs; times and token costs are per-run means.

Notes:

- The baseline's one failure shipped `asyncapi: 3.0.0` when asked for the
  latest version (3.1.0, Jan 2026). The pattern behind it matters more
  than the score: **five of six baseline authoring runs initially wrote
  3.0.0** and only corrected after the AsyncAPI CLI's governance check
  flagged it — the failing run was the one that skipped validation. The
  with-skill arm wrote 3.1.0 first-try in all six authoring runs. Where
  the CLI isn't installed, expect the baseline to ship 3.0.0 (or worse)
  consistently.
- On the hard eval (dynamic request-reply + Avro multi-format), both arms
  scored clean on this strong model, but the skill arm ran ~2x faster
  (53s vs 103s mean) — it doesn't have to rediscover the null-address
  reply-channel idiom or the Avro union syntax.
- With-skill runs cost ~25-35% more tokens (loading references) and show
  zero variance across runs; baseline correctness depends on the agent
  choosing to self-verify against installed tooling.
- The Spectral convention check excludes `org-info-contact` for authoring
  evals: the prompts name no owner, so omitting a contact is honest rather
  than wrong.

Full outputs (gitignored): `.evals/asyncapi-authoring/20260901-2200-r{1,2,3}/`.
