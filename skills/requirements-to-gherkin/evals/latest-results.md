# Eval results: requirements-to-gherkin

Last run: 20260903-190708 UTC via `task eval:skills NAME=requirements-to-gherkin MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| notes-to-gherkin | 10/10 | 9/10 | 5 / 5 | 63.0s / 46.2s | $0.17 / $0.14 |
| session-prep | 7/7 | 5/7 | 5 / 2 | 52.6s / 47.0s | $0.15 / $0.11 |

Grader checks that separated the arms: notes-to-gherkin 1/10, session-prep 2/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.50x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/requirements-to-gherkin/20260903-190708/`.
