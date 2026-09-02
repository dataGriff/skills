# Eval results: openapi-authoring

Last run: 20260902-204716 UTC via `task eval:skills NAME=openapi-authoring MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| author-books-api | 10/10 | 9/10 | 8 / 12 | 42.3s / 64.3s | $0.19 / $0.25 |
| review-legacy-spec | 11/11 | 10/11 | 16 / 9 | 92.7s / 87.6s | $0.34 / $0.25 |

Grader checks that separated the arms: author-books-api 1/10, review-legacy-spec 1/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.19x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/openapi-authoring/20260902-204716/`.
