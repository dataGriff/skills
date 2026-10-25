# Eval results: repo-health

Last run: 20261025-192412 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 22/25 | 24/25 | 79 / 73 | 629.6s / 515.6s | $2.12 / $1.79 |
| healthy-repo-restraint | 9/11 | 9/11 | 36 / 30 | 290.6s / 192.6s | $0.91 / $0.65 |

Grader checks that separated the arms: four-problems-invoicer 2/25, healthy-repo-restraint 2/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.23x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-192412/`.
