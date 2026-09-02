# Eval results: contract-testing-microcks

Last run: 20260902-210906 UTC via `task eval:skills NAME=contract-testing-microcks MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| github-actions-contract-gate | 5/5 | 5/5 | 7 / 10 | 33.4s / 102.1s | $0.16 / $0.25 |
| node-testcontainers-provider-test | 6/6 | 5/6 | 8 / 8 | 51.3s / 77.8s | $0.19 / $0.22 |

Grader checks that separated the arms: github-actions-contract-gate 0/5, node-testcontainers-provider-test 1/6. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.87x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/contract-testing-microcks/20260902-210906/`.

## Notes: initial run (2026-09-02)

- **Separating check.** On the Testcontainers task the baseline hallucinated
  the runner enum (`TestRunnerType.OPENAPI_SCHEMA`); the with-skill arm used
  the real `OPEN_API_SCHEMA`. That id is exactly what Microcks' API expects,
  so the failure would only surface at runtime against a live container.
- **Speed/cost.** Scores otherwise tie, but the skill arm is 3x faster and
  cheaper on the CI task (7 vs 10 turns, 33s vs 102s, $0.16 vs $0.25 - the
  baseline spent turns rediscovering action inputs) and cheaper on the
  Testcontainers task at equal turns. Token ratio 0.87x: the skill pays for
  itself without loading references (both tasks resolved from SKILL.md
  alone; the references are conditional).
- **Grader fix during this run.** The original composite testEndpoint check
  required the literal `"Order API:1.2.0"`; both arms build the id from
  constants, which masked the runner-enum separation. Split into two checks
  (parts of the request; exact runner id) and re-graded the same outputs.
  A Python 3.11 f-string syntax error in grade.py was also fixed before
  grading (runs themselves were unaffected).
