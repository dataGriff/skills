# Eval results: odcs-authoring

Last run: 20260902-200210 UTC via `task eval:skills NAME=odcs-authoring MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| author-orders-contract | 6/6 | 4/6 | 9 / 7 | 42.0s / 61.1s | $0.18 / $0.17 |
| review-legacy-contract | 6/6 | 3/6 | 14 / 11 | 77.6s / 168.6s | $0.25 / $0.36 |

Grader checks that separated the arms: author-orders-contract 2/6, review-legacy-contract 3/6. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.93x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/odcs-authoring/20260902-200210/`.

## Notes: cost slimming (2026-09-02)

Before/after on the same model (`claude-sonnet-5`), same grader, no
`datacontract` CLI available to either arm during the runs (installed
afterwards for grading only). The original SKILL.md said "start from the
template — copy it" and had three "Read references/…" workflow steps; the
slimmed one carries a complete inline skeleton and the v3.1.0 migration
traps, with references opt-in.

| Eval | Turns before → after | Cost before → after | Score |
|------|---------------------|---------------------|-------|
| author-orders-contract | 18 → 9 (baseline 7) | $0.31 → $0.18 (baseline $0.16–0.17) | 6/6 both, baseline 4/6 both |
| review-legacy-contract | 13 → 14 (baseline 11–14) | $0.27 → $0.25 (baseline $0.36–0.41) | 6/6 both, baseline 3/6 both |

Token ratio with skill / baseline: 1.25× → 0.93× — the slimmed skill is
now cheaper than no skill overall, because the baseline burns turns
without the standard's specifics. Unlike gherkin-feature-authoring, the
benefit here is large and repeatable: in both runs the baseline wrote
`apiVersion: v3.0.2` and failed lint on the new contract, and on the
review kept the deprecated `dataProduct`, the list-form `team`, and
failed lint. Checks separating the arms: 2/6 and 3/6, identical across
runs. Review-path turns didn't fall (the task itself needs reading the
legacy file and writing two outputs); authoring dropped by half.

Grader fix in the same change: a missing `datacontract` binary now fails
the lint check with evidence instead of crashing and leaving every arm
unscored, which is what the first measurement attempt did.
