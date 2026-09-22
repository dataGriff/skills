# Eval results: goldratt-4-questions

Last run: 20260904-194916 UTC via `task eval:skills NAME=goldratt-4-questions MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| proposal-review | 8/8 | 8/8 | 6 / 4 | 90.0s / 63.5s | $0.20 / $0.15 |
| adoption-post-mortem | 7/7 | 7/7 | 5 / 6 | 63.3s / 61.4s | $0.16 / $0.16 |

Grader checks that separated the arms: proposal-review 0/8, adoption-post-mortem 0/7. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 0.94x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/goldratt-4-questions/20260904-194916/`.

## Notes on this run

No grader check separated the arms: baseline Sonnet caught every planted
trap (the feature-list pitch, the missing limitation evidence, the
"run both systems in parallel indefinitely" cost-without-benefit plan,
the never-retired old rules). Two honest caveats before reading that as
"the skill adds nothing":

- **The baseline was not skill-free.** `.claude/skills` is a committed
  symlink to `skills/`, so both eval arms run with every skill's
  frontmatter in project context — and this skill's description names
  Goldratt and the four questions. The eval-1 baseline output applied
  "Goldratt's four questions" explicitly by name. For CLI/format skills
  that leakage is negligible; for a thinking-framework skill the
  description is half the payload, so this baseline overstates the
  no-skill case. A clean measurement needs the runner to point baseline
  arms at a cwd outside the repo (or mask the skill's frontmatter) —
  repo-level follow-up, not fixable from inside one skill.
- **What the run does establish:** the skill costs nothing to carry
  (0.94x baseline tokens, ±1–2 turns) and the with-skill outputs follow
  the four-question structure with explicit old-rule/new-rule pairing.
  Its expected value is triggering and consistency — applying the
  framework every time, including on models and phrasings where it
  would not surface unprompted — which these output evals, run on
  Sonnet inside this repo, cannot measure.
