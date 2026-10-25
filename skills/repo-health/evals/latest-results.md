# Eval results: repo-health

Last run: 20261025-162456 UTC via `task eval:skills NAME=repo-health MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| four-problems-invoicer | 23/25 | 15/25 | 71 / 53 | 654.9s / 320.9s | $2.03 / $1.05 |
| healthy-repo-restraint | 11/11 | 3/11 | 36 / 28 | 325.2s / 181.0s | $0.88 / $0.54 |

Grader checks that separated the arms: four-problems-invoicer 10/25, healthy-repo-restraint 8/11. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.90x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-health/20261025-162456/`.
