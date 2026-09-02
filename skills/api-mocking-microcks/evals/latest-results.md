# Eval results: api-mocking-microcks

Last run: 20260901-212116 UTC via `task eval:skills NAME=api-mocking-microcks` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| mock-rest-order-api | 9/9 | 9/9 | 273.1s / 207.3s | $0.72 / $0.49 |
| mock-async-signup-events | 7/7 | 6/7 | 229.7s / 109.4s | $0.56 / $0.23 |

Full outputs (gitignored): `.evals/api-mocking-microcks/20260901-212116/`.

Notes: grading is static against Microcks conventions (container registries
are blocked in the eval sandbox, so no live import). The baseline knows
Microcks well on REST structure; its one failure is the traffic-killing
kind — it declared the AsyncAPI channel as `publish` (events the app
consumes), which Microcks never mocks, so consumers would see zero events.
The skilled arm spent ~1.3-2x the baseline's time and cost reading the
skill; the correctness gap it buys is on the async conventions.
