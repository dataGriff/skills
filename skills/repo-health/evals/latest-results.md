# Eval results: repo-health

Last run: 20261025-112433 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 24/25 | 13/25 | 88 / 48 | 889.3s / 319.6s | $2.80 / $0.88 |
| healthy-repo-restraint | 9/11 | 2/11 | 42 / 28 | 507.6s / 218.6s | $1.26 / $0.57 |

Grader checks that separated the arms: four-problems-invoicer 11/25, healthy-repo-restraint 7/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 3.05x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-112433/`.
