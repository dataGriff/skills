# Eval results: terraform

Last run: 20260902-215402 UTC via `task eval:skills NAME=terraform MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| author-log-bucket-module | 8/8 | 8/8 | 18 / 11 | 105.6s / 65.6s | $0.35 / $0.21 |
| review-legacy-config | 7/7 | 7/7 | 25 / 16 | 255.3s / 252.3s | $0.55 / $0.53 |
| refactor-adopt-backend | 7/7 | 7/7 | 17 / 18 | 118.4s / 121.9s | $0.35 / $0.31 |

Grader checks that separated the arms: author-log-bucket-module 0/8, review-legacy-config 0/7, refactor-adopt-backend 0/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.16x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/terraform/20260902-215402/`.

## Notes: baseline parity on claude-sonnet-5 (2026-09-02)

No grader check separates the arms on this model. That includes two checks
planted specifically because older models get them wrong: S3-backend
locking via `use_lockfile` (baseline did NOT reach for the deprecated
DynamoDB table) and declarative refactoring with `moved`/`import` blocks
(baseline used both, no `state mv` surgery). claude-sonnet-5's baseline
already exhibits every graded behaviour, so the score delta here is noise
by this repo's own rule and the skill's benefit on this model is
unproven — it costs little when triggered (1.16x tokens, a few extra
turns from reading SKILL.md), and its remaining value is the content the
graders don't exercise (state recovery, drift, `terraform test`, CI
shape) and weaker/older models. Re-run against a smaller model before
assuming the parity holds there.

Grader history: the eval-1 AMI check originally required the hardcoded
AMI to be replaced by a variable/lookup; the with-skill arm instead kept
it pinned with a comment explaining that a fresh lookup would force
instance replacement — the safer read of the task's "must keep existing"
constraint — so the check now accepts a deliberately pinned, commented
literal too. Scores above are from re-grading the same run outputs with
that fix.
