# Eval results: api-security

Last run: 20260902-214432 UTC via `task eval:skills NAME=api-security MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| review-orders-api | 15/16 | 14/16 | 9 / 4 | 231.6s / 138.5s | $0.43 / $0.26 |
| fix-auth-and-authz | 8/8 | 7/8 | 13 / 13 | 90.5s / 100.8s | $0.32 / $0.31 |

Grader checks that separated the arms: review-orders-api 3/16, fix-auth-and-authz 1/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.11x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/api-security/20260902-214432/`.
