# Eval results: aws-lambda

Last run: 20260903-050218 UTC via `task eval:skills NAME=aws-lambda MODEL=haiku` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| build-sqs-worker | 11/11 | 9/11 | 10 / 3 | 42.7s / 23.1s | $0.09 / $0.04 |
| review-legacy-lambda | 12/12 | 10/12 | 13 / 9 | 47.9s / 42.9s | $0.10 / $0.07 |

Grader checks that separated the arms: build-sqs-worker 2/11, review-legacy-lambda 2/12. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 2.07x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/aws-lambda/20260903-050218/`.

## Notes

- First graded run scored the with-skill arm 9/11 on build-sqs-worker because
  the grader ignored the SAM `Globals: Function:` block the with-skill arm
  (correctly) used for Runtime/Timeout; the grader now merges Globals into
  function properties and the iteration was re-graded.
- On sonnet (run 20260902-212103, 1.21x tokens), both arms saturated every
  structural check: sonnet already knows these Lambda patterns, so no check
  separated the arms; the with-skill review-legacy-lambda run was merely
  faster and cheaper (91s/$0.25 vs 129s/$0.29). If a future edit needs to
  prove more on strong models, the grader needs behavioural checks (e.g.
  visibility-timeout sizing, alarm wiring) rather than more of these.
- On haiku (run above), the skill separates cleanly — with-skill perfect on
  both evals, baseline dropped 4 checks, and the misses are real production
  bugs, not style: `batchItemFailures` returned with an `itemId` key instead
  of `itemIdentifier` (Lambda treats that as a malformed response and fails
  the whole batch), an SQS event source without `ReportBatchItemFailures`
  (failure reporting silently ignored, failed messages deleted), and an
  outdated runtime pin. Net: the skill's value concentrates on
  weaker/faster models and on exactly the silent-failure details.
