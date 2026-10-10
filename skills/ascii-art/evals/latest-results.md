# Eval results: ascii-art

Last run: 20261010-004653 UTC via `task eval:skills NAME=ascii-art MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-5-5, claude-sonnet-5-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| cli-banner | 12/12 | 11/12 | 4 / 6 | 18.1s / 18.4s | $0.08 / $0.08 |
| readme-mascot | 13/13 | 11/13 | 6 / 4 | 37.5s / 15.3s | $0.10 / $0.06 |
| image-to-ascii | 12/12 | 12/12 | 6 / 3 | 22.0s / 20.8s | $0.10 / $0.06 |

Grader checks that separated the arms: cli-banner 1/12, readme-mascot 2/13, image-to-ascii 0/12. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.64x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/ascii-art/20261010-004653/`.

## Notes on this run

- **What separated the arms.** The baseline hand-lettered the banner (its
  letters are only 5 rows with thin strokes, so three rows carried enough
  ink to count) and added an unrequested `N I G H T W A T C H` caption
  under the owl, tripping the stray-letters check; the with-skill arm
  generated the banner with `scripts/asciiart.py banner` and framed it with
  `box`, giving an exactly rectangular result. Both arms converted the
  image correctly: baseline Sonnet wrote its own Pillow script, the skill
  arm used the bundled one.
- **Cost.** The skill arm spent 1.64x the baseline's tokens and one or two
  extra turns per task, which is reading SKILL.md and running the toolkit;
  no reference file was loaded in any run, so the opt-in routing holds.
- **Caveat.** `.claude/skills` is a committed symlink to `skills/`, so the
  baseline arm still carries this skill's description in project context
  (see the goldratt-4-questions results for the same caveat). A clean
  no-skill baseline needs the runner to point baseline arms outside the
  repo.
- **What these evals cannot measure.** The hand-drawn owl is graded on
  mechanics (rows, width, symmetric eyes, a branch), not on whether it
  looks like an owl; a human look at `.evals/ascii-art/<stamp>/` is still
  the real test of the craft guidance.
