# Eval results: gherkin-feature-authoring

Last run: 20260902-054258 UTC via `task eval:skills NAME=gherkin-feature-authoring MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| story-to-feature | 8/8 | 7/8 | 39.9s / 19.8s | $0.15 / $0.07 |
| review-and-rewrite | 9/9 | 9/9 | 65.2s / 53.1s | $0.19 / $0.13 |

Full outputs (gitignored): `.evals/gherkin-feature-authoring/20260902-054258/`.

Notes: run pinned to `claude-sonnet-5` via the new `MODEL=` support in
`task eval:skills`, after the session's default model changed. (A prior
attempt at this pin scored 0/1 and 2/9 — not a real result: the headless
CLI refused to read `/home/user/skills` at all under `acceptEdits`, a
sandbox boundary the previous default model didn't hit. Fixed by passing
`--add-dir` to the with-skill arm; see `scripts/eval_skills.py`.) With
that fixed, the baseline again failed only the recurring `Rule:` block
check on story-to-feature, but this time matched the skill 9/9 on
review-and-rewrite — a genuinely good independent rewrite that kept all
three behaviours. Consistent with the variance-benchmark finding below:
on a strong model the skill's floor-raising effect shrinks to near zero on
tasks the model already handles well unaided.

## Variance benchmark (2026-09-02, 4 runs per eval per arm)

16 independent subagent runs (4 × story-to-feature, 4 × review-and-rewrite,
with-skill vs no-skill), graded with the same grader:

| Metric | With skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Pass rate | 100% ± 0% | 100% ± 0% | 0 |
| Time | 68.3s ± 5.7s | 34.1s ± 15.4s | +34.1s |
| Tokens | 49,540 ± 603 | 40,915 ± 1,228 | +8,626 (~21%) |

Every baseline run passed every check — including Rule: blocks and
behaviour preservation, the checks baselines failed in earlier claude-CLI
runs (see above and history). Those subagents ran on a stronger model
than the CLI's headless default, so the honest conclusion is that the
skill's measurable value is model-dependent: on a top-tier model these
tasks saturate the grader with or without it (the skill then costs ~21%
more tokens for no measured gain, confirmed again on the pinned Sonnet
run above); on a weaker executor the baseline reliably dropped a
behaviour or structure the skill preserved. What the grader cannot
measure: with-skill runs consistently flagged the fixture's missing-Then
scenario as an open question for the business instead of silently
inventing an outcome; most baselines did not.
