# Eval results: repo-health

Last run: 20261025-125523 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 25/25 | 13/25 | 62 / 50 | 643.7s / 301.3s | $1.84 / $0.95 |
| healthy-repo-restraint | 6/11 | 3/11 | 23 / 20 | 354.3s / 150.3s | $0.76 / $0.42 |

Grader checks that separated the arms: four-problems-invoicer 12/25, healthy-repo-restraint 5/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.75x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-125523/`.
