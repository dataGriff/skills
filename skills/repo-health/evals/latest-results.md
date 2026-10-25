# Eval results: repo-health

Last run: 20261025-203239 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 23/25 | 23/25 | 64 / 67 | 543.4s / 512.5s | $1.83 / $1.73 |
| healthy-repo-restraint | 9/11 | 6/11 | 29 / 27 | 231.3s / 171.1s | $0.73 / $0.53 |

Grader checks that separated the arms: four-problems-invoicer 2/25, healthy-repo-restraint 5/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.12x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-203239/`.
