# Eval results: repo-consistency-checker

Last run: 20260912-073930 UTC via `task eval:skills NAME=repo-consistency-checker MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| audit-report | 17/18 | 17/18 | 19 / 16 | 172.8s / 140.3s | $0.47 / $0.33 |
| audit-and-fix | 16/16 | 16/16 | 42 / 35 | 257.2s / 215.2s | $0.93 / $0.74 |

Grader checks that separated the arms: audit-report 0/18, audit-and-fix 0/16. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.37x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-consistency-checker/20260912-073930/`.
## Notes: first evals (2026-09-12)

Fixture: a ten-file "widgets" service with thirteen planted problems —
a wrong `make` target, a config file named by the wrong name, a port that
disagrees with config, a docstring and a comment contradicting the code
(both pinned by tests), a Python version that differs between two docs, a
setup section duplicated verbatim, the wrong lint tool, a dead helper,
a commented-out block, a done TODO, two docs describing a removed worker,
and an unused config key — plus a CHANGELOG that records the old values
as history and must not be flagged.

- **On Sonnet 5 the fixture does not separate the arms.** Both arms
  found every plant, cited file:line on both sides, treated the CHANGELOG
  as history and wrote a coverage note (18/18 report, 16/16 fix). A
  ten-file repo is small enough that the baseline simply reads everything,
  which is the skill's own step 3; the skill's mechanical scan and
  findings format add structure but no extra finds here. The with-skill
  arm cost ~1.4× the tokens and three to seven more turns (running the
  scan, opening a reference).
- **Grader defect fixed after the first grading.** The "CHANGELOG not
  flagged" check matched prose that merely cited the changelog as
  evidence; it now only looks at finding rows and headings whose claim
  side names `CHANGELOG.md:<line>`. Both arms were regraded on the same
  outputs.
- **What would separate the arms.** A fixture too large to read in full
  (so the scan's broken-reference, undefined-command and duplicate
  detection actually saves turns), paraphrased rather than verbatim
  duplicates, and a doc-right / code-wrong case whose test is missing (the
  "possible bug" direction call). Until then, treat this eval as a
  regression check on the skill's format, not as proof it beats the
  baseline on a strong model.
