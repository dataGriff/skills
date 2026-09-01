# Eval results: asyncapi-authoring

Last run: 2026-09-01 UTC, iteration 20260901-212212 (run via session
subagents; rerun with `task eval:skills NAME=asyncapi-authoring` — commit
this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| author-inventory-asyncapi | 7/7 | 6/7 | 37.9s / 28.5s | ? / ? |
| review-legacy-asyncapi | 7/7 | 7/7 | 115.0s / 171.1s | ? / ? |

Notes: the baseline's one failure targeted AsyncAPI 3.0.0 despite being
asked for the latest version (3.1.0, Jan 2026) — the knowledge-currency
gap the skill closes. Both arms had the AsyncAPI CLI on PATH and baselines
matched on the review eval largely by self-verifying against it (at ~1.5x
the wall clock on the review task); expect a larger correctness gap where
the CLI isn't installed, especially on the v2 publish/subscribe inversion.

Full outputs (gitignored): `.evals/asyncapi-authoring/20260901-212212/`.
