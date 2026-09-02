# Eval results: gherkin-feature-authoring

Last run: 20260901-211400 UTC via `task eval:skills NAME=gherkin-feature-authoring` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| story-to-feature | 10/10 | 6/10 | 64.2s / 10.5s | $0.30 / $0.06 |
| review-and-rewrite | 10/10 | 8/10 | 154.2s / 60.5s | $0.44 / $0.14 |

Full outputs (gitignored): `.evals/gherkin-feature-authoring/20260901-211400/`.

Notes: same outputs as the original run, re-graded after tightening the
grader — the first grader's purely structural checks were easy enough that
the baseline near-tied (6/7, 7/8), understating a visible quality gap. The
added checks catch what review of the outputs showed: the baseline welded
payment-then-shipping into one two-When scenario, duplicated a scenario
shape instead of using an outline, never exercised a discount amount, made
no rules explicit, and dropped the order-history behaviour in the rewrite.
The with-skill arms pass all added checks unchanged. SKILL.md was slimmed
(122 → 82 lines) after this run without changing its guidance; a fresh
end-to-end re-run is pending (blocked at time of commit by the claude CLI
session limit).
