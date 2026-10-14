# Eval results: bdd-python-testing

Last run: 20260902-212231 UTC via `task eval:skills NAME=bdd-python-testing MODEL=haiku` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| pytest-bdd-wiring | 8/8 | 7/8 | 14 / 24 | 60.0s / 79.8s | $0.12 / $0.19 |
| behave-wiring | 8/8 | 8/8 | 21 / 21 | 81.9s / 66.8s | $0.18 / $0.15 |

Grader checks that separated the arms: pytest-bdd-wiring 1/8, behave-wiring 0/8. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.80x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/bdd-python-testing/20260902-212231/`.

## Notes

- A pinned-Sonnet run (20260902-211235) scored 8/8 on all four arms with 0
  separating checks: Sonnet wires standard pytest-bdd/behave tasks correctly
  without the skill, at 1.36x tokens with it (sonnet: 9/6 and 18/12 turns,
  the overhead being the SKILL.md read itself — no unconditional reference
  loads showed up).
- On Haiku (table above) the skill separates on state discipline
  (baseline skipped `target_fixture`) and is net cheaper: fewer turns and
  0.80x tokens, because the workflow steers straight to a passing suite.
- Both fixtures' graders are behavioural (the suite is actually executed),
  so the saturation on Sonnet is a task-difficulty ceiling, not a grader
  gap; harder evals (flaky layout, async steps, existing broken glue) would
  be the way to separate stronger models.
