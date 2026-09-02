# Eval results: api-mocking-microcks

Last run: 20260902-055552 UTC via `task eval:skills NAME=api-mocking-microcks` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| json-body-dispatch | 0/1 | 7/8 | 35.2s / 224.2s | $0.15 / $0.52 |
| mock-async-signup-events | 5/7 | 0/1 | 207.8s / 0.3s | $0.45 / $0.00 |
| overlay-generated-spec | 1/7 | 1/7 | 0.5s / 0.4s | $0.00 / $0.00 |
| testcontainers-contract-wiring | 0/1 | 0/1 | 0.3s / 0.3s | $0.00 / $0.00 |

Full outputs (gitignored): `.evals/api-mocking-microcks/20260902-055552/`.
