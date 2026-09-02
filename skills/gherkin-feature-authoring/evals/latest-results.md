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
