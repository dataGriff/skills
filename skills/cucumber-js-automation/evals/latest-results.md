# Eval results: cucumber-js-automation

Last run: 20260902-211219 UTC via `task eval:skills NAME=cucumber-js-automation MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| implement-steps | 6/6 | 6/6 | 16 / 13 | 69.1s / 58.9s | $0.23 / $0.18 |
| spec-and-steps | 8/8 | 7/8 | 15 / 19 | 85.9s / 121.6s | $0.27 / $0.36 |

Grader checks that separated the arms: implement-steps 0/6, spec-and-steps 1/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.82x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/cucumber-js-automation/20260902-211219/`.

## Notes

- The separating check: the baseline leaked implementation jargon
  ("pence") into its feature file on spec-and-steps; the with-skill arm
  stayed in business language and beat the baseline on turns, time, and
  cost there (15 vs 19 turns, $0.27 vs $0.36).
- implement-steps ties 6/6 on claude-sonnet-5 — a strong model passes the
  structural checks unaided; the skill's margin shows on the
  spec-authoring half and on cost (0.82x tokens overall).
