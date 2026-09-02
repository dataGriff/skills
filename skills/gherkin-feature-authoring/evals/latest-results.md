# Eval results: gherkin-feature-authoring

Last run: 20260902-161403 UTC via `task eval:skills NAME=gherkin-feature-authoring MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| story-to-feature | 8/8 | 7/8 | 5 / 2 | 28.0s / 11.1s | $0.13 / $0.06 |
| review-and-rewrite | 9/9 | 9/9 | 10 / 5 | 93.2s / 67.3s | $0.25 / $0.16 |

Grader checks that separated the arms: story-to-feature 1/8, review-and-rewrite 0/9. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.71x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/gherkin-feature-authoring/20260902-161403/`.

## Notes: making the skill cheaper (2026-09-02)

The original SKILL.md forced three file loads per use (template, style.md,
then a checklist walk): 6–8 tool turns against the baseline's 2–4. Two
slimming passes moved the rules that actually changed outcomes into
SKILL.md itself (explicit `Rule:` blocks, one When, preserve every
behaviour in a rewrite with its own When, flag unknown outcomes as
questions) plus an inline example and the smell names a review needs;
references are now opt-in. Measured on Sonnet against the original:

- **story-to-feature**: 6 turns / $0.15 / 40s → 4–5 turns / $0.11–0.13 /
  25–28s (≈25% cheaper, ≈35% faster), score unchanged at 8/8 while the
  baseline scored 7/8 in both samples (no `Rule:` blocks — the one
  consistent gap).
- **review-and-rewrite**: not cheaper — 10–11 turns, ≈1.5× the baseline's
  cost, the same ratio as before slimming (both arms drifted up in
  absolute cost this run). The benefit here is the clearest we have: the
  baseline folded or dropped the order-history behaviour in 2 of 5 Sonnet
  samples across all runs; the skill with the sharpened rule 5 kept it in
  every sample (an earlier slim-1 wording let it fold once — fixed).

The remaining review-path cost is the model still opening references
during reviews; the next lever would be forbidding that outright, at some
risk to review quality. Not done — unmeasured changes are how the earlier
false readings happened.

## Caveats and history

- **Model identity.** The CLI's headless default silently became
  `claude-sonnet-5` mid-investigation (after a `/model` switch in the
  interactive session), and the two earliest runs (2026-09-01, 2026-09-02
  05:03) never recorded which model served them. Their baseline failures
  (no `Rule:` blocks, dropped behaviour, two-When journey) are real but
  cannot be attributed to a specific model. Every run now records served
  models (see the header).
- **Variance benchmark** (16 subagent runs on the session's own model, 4
  per eval per arm, pre-slimming): 100% ± 0% pass rate in *both* arms;
  skill cost +21% tokens, +34s. On that executor the tasks saturated the
  grader with or without the skill.
- **Single-sample runs are noisy** — the Sonnet baseline has scored
  anywhere from 7/9 to 9/9 on the same rewrite task. Treat one-run deltas
  as directional.
