# Eval results: aws-lambda

Last run: 20260902-212103 UTC via `task eval:skills NAME=aws-lambda MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| build-sqs-worker | 11/11 | 11/11 | 18 / 14 | 87.5s / 87.1s | $0.33 / $0.26 |
| review-legacy-lambda | 12/12 | 12/12 | 10 / 10 | 91.1s / 128.9s | $0.25 / $0.29 |

Grader checks that separated the arms: build-sqs-worker 0/11, review-legacy-lambda 0/12. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.21x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/aws-lambda/20260902-212103/`.

## Notes

- First graded run scored the with-skill arm 9/11 on build-sqs-worker because
  the grader ignored the SAM `Globals: Function:` block the with-skill arm
  (correctly) used for Runtime/Timeout; the grader now merges Globals into
  function properties and the iteration was re-graded.
- On sonnet, both arms saturate every structural check: the baseline model
  already knows these Lambda patterns, so no grader check separated the arms
  on this run. The observable deltas are softer — the with-skill
  review-legacy-lambda run was faster and cheaper (91s/$0.25 vs 129s/$0.29),
  and per-run token cost sits at 1.21x with all reference loads conditional.
  If a future edit needs to prove more, the grader needs behavioural checks
  (e.g. weaker models, or checks on visibility-timeout sizing and alarm
  wiring) rather than more of these.
