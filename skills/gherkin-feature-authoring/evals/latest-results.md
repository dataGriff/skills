# Eval results: gherkin-feature-authoring

Last run: 20260902-050316 UTC via `task eval:skills NAME=gherkin-feature-authoring` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| story-to-feature | 8/8 | 7/8 | 86.4s / 16.8s | $0.35 / $0.07 |
| review-and-rewrite | 9/9 | 7/9 | 160.4s / 55.3s | $0.39 / $0.15 |

Full outputs (gitignored): `.evals/gherkin-feature-authoring/20260902-050316/`.

Notes: fresh end-to-end run with the slimmed SKILL.md (122 → 82 lines) and
the tightened grader. Two checks added in the first tightening pass turned
out to be overfit to one run's outputs — a duplicate-scenario-shape
heuristic and an explicit-discount-amount requirement both failed the
with-skill arm on defensible files — and were removed; a check both arms
fail on good output is noise, not signal. The surviving discriminators are
behavioural: the baseline again wrote no Rule: blocks for a four-rule story,
collapsed the rewrite to two scenarios, and dropped the order-history
behaviour instead of keeping it as its own scenario. Single-sample runs are
non-deterministic; the with-skill arm has passed every surviving check in
both runs.

## Variance benchmark (2026-09-02, 4 runs per eval per arm)

16 independent subagent runs (4 × story-to-feature, 4 × review-and-rewrite,
with-skill vs no-skill), graded with the same grader:

| Metric | With skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Pass rate | 100% ± 0% | 100% ± 0% | 0 |
| Time | 68.3s ± 5.7s | 34.1s ± 15.4s | +34.1s |
| Tokens | 49,540 ± 603 | 40,915 ± 1,228 | +8,626 (~21%) |

Every baseline run passed every check — including Rule: blocks and
behaviour preservation, the checks baselines failed in both claude-CLI
runs above. The subagent runs used a stronger model than the CLI default,
so the honest conclusion is that the skill's measurable value is
model-dependent: on a top-tier model these tasks saturate the grader with
or without it (the skill then costs ~21% more tokens for no measured
gain); on the weaker CLI executor the baseline reliably dropped a
behaviour or structure the skill preserved. What the grader cannot
measure: with-skill runs consistently flagged the fixture's missing-Then
scenario as an open question for the business instead of silently
inventing an outcome; most baselines did not.
