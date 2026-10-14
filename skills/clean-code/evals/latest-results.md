# Eval results: clean-code

Last run: 20260903-050134 UTC via `task eval:skills NAME=clean-code MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| construct-module | 10/10 | 9/10 | 6 / 5 | 37.6s / 28.8s | $0.15 / $0.12 |
| refactor-legacy | 9/10 | 9/10 | 6 / 5 | 39.0s / 22.4s | $0.14 / $0.11 |
| review-code | 10/10 | 9/10 | 7 / 4 | 59.1s / 53.8s | $0.18 / $0.14 |

Grader checks that separated the arms: construct-module 1/10, refactor-legacy 0/10, review-code 1/10. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.22x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/clean-code/20260903-050134/`.

## Notes (2026-09-03 run)

Sonnet's baseline is already strong on clean-code tasks, so margins are
small by design: the skill arm won 29/30 vs 27/30. Checks that separated:
the baseline wrote a 48-line function where the skill arm stayed small
(construct-module), and the baseline review missed the magic-values
defect class (review-code). Both refactor arms failed the same single
check — each named the rate constants but left `86400` inline — so
refactor-legacy showed no separation this run. Review-code cost 7 turns
vs 4: the extra turns are the conditional read of SKILL.md plus
references/code-smells.md, which that mode legitimately needs.
