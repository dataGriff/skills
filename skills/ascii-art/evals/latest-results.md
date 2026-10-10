# Eval results: ascii-art

Last run: 20261010-011021 UTC via `task eval:skills NAME=ascii-art MODEL=sonnet` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-5-5, claude-sonnet-5-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| cli-banner | 12/12 | 11/12 | 4 / 5 | 23.3s / 21.7s | $0.09 / $0.07 |
| readme-mascot | 18/18 | 18/18 | 12 / 6 | 78.2s / 23.4s | $0.21 / $0.07 |
| image-to-ascii | 12/12 | 12/12 | 5 / 3 | 22.9s / 10.2s | $0.10 / $0.05 |

Grader checks that separated the arms: cli-banner 1/12, readme-mascot 0/18, image-to-ascii 0/12. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.76x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/ascii-art/20261010-011021/`.

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

## Notes on this run

Second iteration: SKILL.md gained the "Give it character" section (fill
the space, feature list, interior texture, overlap, a prop, count strokes,
no captions) after the first run's skill-arm owl was correct but sparse,
and the mascot grader gained five richness checks to match.

- **Mascot.** The skill arm's owl now has textured wings that overlap the
  body, brows, talons gripping a drawn branch and ground marks, and passes
  every richness check; the first run's owl would have failed two of them.
  The baseline drew an equally rich owl this time, so the two arms tie on
  the grader and the eye looks about equally well on both. What changed
  is the floor, not the ceiling: the guidance makes the detailed version
  the default rather than the lucky draw.
- **Cost.** That guidance is paid for: 12 turns and 78 s against 6 and
  23 s for the baseline on the mascot task (1.76x tokens over the suite,
  up from 1.64x). The extra turns are the detail pass and linting, not
  reference loads; the trade is deliberate for a drawing task, and the
  banner and image tasks stay within one or two turns of the baseline.
- **Banner and image.** Unchanged from the first run: the generated
  banner is the one check that separates the arms; both arms convert the
  image equally well. The grader now maps the image through a top-aligned
  2:1 grid so trimming trailing blank rows is not penalised.
- **Caveat.** The baseline still sees this skill's description through the
  committed `.claude/skills` symlink, so it is not a clean no-skill arm.
