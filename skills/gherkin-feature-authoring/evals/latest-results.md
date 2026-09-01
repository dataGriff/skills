# Eval results: gherkin-feature-authoring

Last run: 20260901-211400 UTC via `task eval:skills NAME=gherkin-feature-authoring` (commit this file with the skill change so the PR carries the evidence).

| Eval | With skill | Baseline | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|-------------------|-------------------|
| story-to-feature | 7/7 | 6/7 | 64.2s / 10.5s | $0.30 / $0.06 |
| review-and-rewrite | 8/8 | 7/8 | 154.2s / 60.5s | $0.44 / $0.14 |

Full outputs (gitignored): `.evals/gherkin-feature-authoring/20260901-211400/`.

Notes: the skill passed every expectation in both evals. The baseline wrote
a scenario with two When/Then cycles in story-to-feature (the
award-on-shipping criterion), and its review-and-rewrite dropped one of the
three behaviours instead of rewriting it. Baselines are faster/cheaper, as
expected for structural checks a strong model mostly satisfies anyway; the
skill's value is the last mile of style discipline.
