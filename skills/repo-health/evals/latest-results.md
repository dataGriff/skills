# Eval results: repo-health

Last run: 20261025-103559 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 16/25 | 13/25 | 93 / 51 | 727.6s / 321.5s | $2.74 / $1.07 |
| healthy-repo-restraint | 3/11 | 2/11 | 30 / 41 | 311.6s / 382.5s | $0.87 / $0.95 |

Grader checks that separated the arms: four-problems-invoicer 5/25, healthy-repo-restraint 3/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.93x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-103559/`.
