# Eval results: repo-health

Last run: 20261025-235731 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 23/25 | 15/25 | 87 / 42 | 519.7s / 320.5s | $2.10 / $0.97 |
| healthy-repo-restraint | 11/11 | 9/11 | 40 / 26 | 172.1s / 262.2s | $0.69 / $0.63 |
| scattered-commands-tooling | 14/14 | 9/14 | 59 / 38 | 815.3s / 275.0s | $2.30 / $0.80 |

Grader checks that separated the arms: four-problems-invoicer 8/25, healthy-repo-restraint 2/11, scattered-commands-tooling 5/14. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 2.68x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-235731/`.
