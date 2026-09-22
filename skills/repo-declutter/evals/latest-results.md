# Eval results: repo-declutter

Last run: 20260922-202938 UTC via `task eval:skills NAME=repo-declutter MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| doc-heavy-service | 11/11 | 6/11 | 42 / 29 | 293.3s / 253.2s | $0.87 / $0.69 |
| noisy-python-module | 13/13 | 11/13 | 13 / 9 | 71.9s / 63.6s | $0.24 / $0.18 |

Grader checks that separated the arms: doc-heavy-service 5/11, noisy-python-module 2/13. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.19x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Downstream tasks - the same follow-up jobs run in the fixture repo before the restructure, after the baseline arm's restructure, and after the skill arm's (means per run; adherence = grader checks the answers passed). This is the cost the skill is meant to reduce: what a later agent pays to orient and whether it follows the repo's rules.

| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |
|------|-------|------|-----------|-------|--------------------------|--------|------|
| doc-heavy-service | before | 2 | 6/6 | 7.5 | 5.5 | 189,332 | $0.09 |
| doc-heavy-service | after-baseline | 2 | 6/6 | 8.0 | 6.0 | 190,622 | $0.10 |
| doc-heavy-service | after-skill | 2 | 6/6 | 8.0 | 6.0 | 172,954 | $0.10 |

Full outputs (gitignored): `.evals/repo-declutter/20260922-202938/`.

## Notes: first evals (2026-09-22)

Two fixtures. A doc-heavy service (README, two docs, CONTRIBUTING; seeded
with 31 hedges, a History section, a "how we got here" section, a dated
migration diary, duplicated install steps, and ten protected facts) and a
noisy Python module (banner, attributions, restating comments, a
commented-out implementation, a stale TODO, `calc(d, r, f)` explained by a
comment, two protected constraint comments, six passing tests).

- **Docs: the skill's discipline shows.** 11/11 against 6/11, five checks
  separating. The baseline trimmed well (README to 61% of its size) but
  left "Previously we used Flask", "as of v2" and the "How we got here"
  section in place, kept changelog-style headings, wrote no findings
  table, and did not commit per category. The skill arm moved every
  history item out with the gist preserved, took the README to 44%, and
  kept all ten protected facts.
- **Code: outcome equal, process different.** 13/13 against 11/13, and
  the two separating checks are both about the audit file. The baseline
  removed the same noise, renamed the same parameters, kept the same
  constraint comments and left the tests green. On a file this small the
  skill's marginal value is the audit and the protected-kept list, not a
  better cleanse. That is worth knowing before paying 1.4x the turns for
  it on a single file; the audit earns its cost when the change is large
  enough to need a reviewer's map.
- **Downstream: modest.** Orienting in the decluttered docs cost the same
  turns and reads as before (the agent reads the same files either way)
  and about 9% fewer tokens (173k against 189k). Adherence was 6/6 in
  every state: the fixture's facts were never hard to find, only
  expensive to read. Decluttering buys tokens per read, not fewer reads;
  fewer reads is the `repo-optimization` skill's job.
- **Cost of running it.** 1.19x the baseline's tokens; 42 against 29 turns
  on docs, 13 against 9 on code. The extra turns are the audit, the
  per-category commits and the test runs the skill requires.
- **Not measured.** Whether the protected-content rule holds on a repo
  where the signal is subtler than a licence header or a ticket-referenced
  comment; other languages than Python; a repo with real git history to
  check "git holds" against (both fixtures start without one).
