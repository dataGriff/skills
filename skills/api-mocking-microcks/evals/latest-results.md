# Eval results: api-mocking-microcks

Last run: 20260902-052832 UTC via `task eval:skills NAME=api-mocking-microcks` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| json-body-dispatch | 6/8 | 7/8 | 236.6s / 173.7s | $0.53 / $0.39 |
| mock-async-signup-events | 7/7 | 7/7 | 194.9s / 104.3s | $0.44 / $0.19 |
| overlay-generated-spec | 1/2 | 1/2 | 269.5s / 175.4s | $0.67 / $0.38 |
| testcontainers-contract-wiring | 6/7 | 6/7 | 102.5s / 123.3s | $0.28 / $0.27 |

Full outputs (gitignored): `.evals/api-mocking-microcks/20260902-052832/`.
