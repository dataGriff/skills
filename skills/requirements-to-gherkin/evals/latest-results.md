# Eval results: requirements-to-gherkin

Last run: 20260903-193254 UTC via `task eval:skills NAME=requirements-to-gherkin MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| notes-to-gherkin | 10/10 | 9/10 | 6 / 4 | 91.8s / 41.8s | $0.21 / $0.12 |
| session-prep | 7/7 | 6/7 | 4 / 3 | 67.0s / 60.7s | $0.16 / $0.13 |

Grader checks that separated the arms: notes-to-gherkin 1/10, session-prep 1/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.41x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/requirements-to-gherkin/20260903-193254/`.
