# Eval results: repo-health

Last run: 20261025-222025 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 23/25 | 23/25 | 91 / 86 | 562.2s / 575.6s | $2.21 / $2.06 |
| healthy-repo-restraint | 11/11 | 2/11 | 31 / 20 | 173.6s / 172.1s | $0.59 / $0.44 |
| scattered-commands-tooling | 9/14 | 9/14 | 48 / 49 | 646.2s / 350.1s | $1.66 / $1.07 |

Grader checks that separated the arms: four-problems-invoicer 2/25, healthy-repo-restraint 9/11, scattered-commands-tooling 0/14. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.21x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-222025/`.
