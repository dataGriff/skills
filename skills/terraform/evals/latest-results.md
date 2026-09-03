# Eval results: terraform

Last run: 20260903-050018 UTC via `task eval:skills NAME=terraform MODEL=claude-haiku-4-5-20251001` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| author-log-bucket-module | 6/8 | 8/8 | 17 / 6 | 74.4s / 38.1s | $0.12 / $0.06 |
| review-legacy-config | 6/7 | 5/7 | 18 / 10 | 101.9s / 95.3s | $0.15 / $0.12 |
| refactor-adopt-backend | 7/7 | 3/7 | 15 / 8 | 58.2s / 35.2s | $0.11 / $0.06 |

Grader checks that separated the arms: author-log-bucket-module 2/8, review-legacy-config 1/7, refactor-adopt-backend 4/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 2.29x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/terraform/20260903-050018/`.

## Notes: model-dependent value (2026-09-03)

Two runs, same evals and grader, different models.

**claude-sonnet-5 (2026-09-02): baseline parity.** 0 separating checks on
all three evals; sonnet's baseline already got even the currency traps
right (S3 `use_lockfile` over the deprecated DynamoDB table, `moved`/
`import` blocks over `state mv`). Token ratio 1.16x. On this model the
skill's graded benefit is nil; its residual value is the ungraded content
(state recovery, drift, `terraform test`, CI shape).

| Eval | With skill | Baseline | Turns (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|
| author-log-bucket-module | 8/8 | 8/8 | 18 / 11 | $0.35 / $0.21 |
| review-legacy-config | 7/7 | 7/7 | 25 / 16 | $0.55 / $0.53 |
| refactor-adopt-backend | 7/7 | 7/7 | 17 / 18 | $0.35 / $0.31 |

**claude-haiku-4-5 (2026-09-03, the table above): the skill earns its
keep.** On the refactor/adopt/backend eval the baseline used the
deprecated DynamoDB lock table, no `moved` block, no `import` block, and
skipped `-migrate-state` in its notes (3/7); with the skill all 7 pass —
4 separating checks, all in the skill's favour, on exactly the state
discipline SKILL.md carries. The review eval separates 1 check (baseline
kept `count` over the list). The authoring eval separates 2 checks
*against* the skill arm — but both trace to an extra `example.tf` usage
file it volunteered (containing a provider block and left unformatted);
the module files themselves pass every check. The 2.29x token ratio is
haiku's small baseline denominator plus the skill read, not runaway
loading (turns 15-18 vs the sonnet arm's 17-25).

Verdict: keep the skill for the state/refactoring/backend knowledge —
that's where models demonstrably go wrong and where mistakes are the
most expensive in real use. On strong current models it is roughly cost-
neutral insurance; on smaller/older models it is a clear win.

Grader history: the eval-1 AMI check originally required the hardcoded
AMI to be replaced by a variable/lookup; the sonnet with-skill arm
instead kept it pinned with a comment explaining that a fresh lookup
would force instance replacement — the safer read of the task's "must
keep existing" constraint — so the check now accepts a deliberately
pinned, commented literal too.
