# Eval results: repo-health

Last run: 20261025-210411 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 23/25 | 23/25 | 84 / 64 | 623.8s / 360.5s | $2.04 / $1.27 |
| healthy-repo-restraint | 11/11 | 9/11 | 28 / 29 | 167.0s / 233.0s | $0.60 / $0.64 |
| scattered-commands-tooling | 11/14 | 3/14 | 65 / 34 | 823.8s / 234.1s | $2.29 / $0.73 |

Grader checks that separated the arms: four-problems-invoicer 2/25, healthy-repo-restraint 2/11, scattered-commands-tooling 8/14. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.86x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-210411/`.
