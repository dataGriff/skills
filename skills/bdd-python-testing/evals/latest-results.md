# Eval results: bdd-python-testing

Last run: 20260902-211235 UTC via `task eval:skills NAME=bdd-python-testing MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| pytest-bdd-wiring | 8/8 | 8/8 | 9 / 6 | 23.0s / 27.3s | $0.15 / $0.13 |
| behave-wiring | 8/8 | 8/8 | 18 / 12 | 83.7s / 57.9s | $0.32 / $0.22 |

Grader checks that separated the arms: pytest-bdd-wiring 0/8, behave-wiring 0/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.36x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/bdd-python-testing/20260902-211235/`.
