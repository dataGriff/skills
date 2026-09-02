# Eval results: api-security

Last run: 20260902-213343 UTC via `task eval:skills NAME=api-security MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| review-orders-api | 14/14 | 13/14 | 9 / 4 | 163.8s / 91.7s | $0.34 / $0.20 |
| fix-auth-and-authz | 7/8 | 7/8 | 20 / 13 | 136.4s / 88.1s | $0.43 / $0.29 |

Grader checks that separated the arms: review-orders-api 1/14, fix-auth-and-authz 0/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.42x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/api-security/20260902-213343/`.
