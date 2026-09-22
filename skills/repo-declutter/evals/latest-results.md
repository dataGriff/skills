# Eval results: repo-declutter

Last run: 20260922-205714 UTC via `task eval:skills NAME=repo-declutter MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| doc-heavy-service | 10/10 | 6/10 | 38 / 40 | 245.3s / 233.9s | $0.87 / $0.80 |
| noisy-python-module | 13/13 | 12/13 | 13 / 9 | 99.7s / 52.0s | $0.27 / $0.16 |

Grader checks that separated the arms: doc-heavy-service 4/10, noisy-python-module 1/13. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.07x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Downstream tasks - the same follow-up jobs run in the fixture repo before the restructure, after the baseline arm's restructure, and after the skill arm's (means per run; adherence = grader checks the answers passed). This is the cost the skill is meant to reduce: what a later agent pays to orient and whether it follows the repo's rules.

| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |
|------|-------|------|-----------|-------|--------------------------|--------|------|
| doc-heavy-service | before | 2 | 6/6 | 7.0 | 5.0 | 167,035 | $0.09 |
| doc-heavy-service | after-baseline | 2 | 6/6 | 8.0 | 6.0 | 190,124 | $0.10 |
| doc-heavy-service | after-skill | 2 | 6/6 | 8.0 | 6.0 | 170,672 | $0.09 |

Full outputs (gitignored): `.evals/repo-declutter/20260922-205714/`.

## Notes: first evals (2026-09-22)

Two fixtures. A doc-heavy service (README, two docs, CONTRIBUTING; seeded
with 31 hedges, a History section, a "how we got here" section, a dated
migration diary and ten protected facts) and a noisy Python module (banner,
attributions, restating comments, a commented-out implementation, a stale
TODO, `calc(d, r, f)` explained by a comment, two protected constraint
comments, six passing tests). This run is on the skill after duplicated
facts were handed to `repo-consistency-checker`, which had landed on main
with an overlapping scope; the first run (11/11 and 13/13 against 6/11 and
11/13) is superseded.

- **Docs: the skill's discipline shows.** 10/10 against 6/10, four checks
  separating. The baseline trimmed well (README to 62%) but left "as of
  v2" and the event-sourcing story in place, wrote an audit with a single
  category, and committed by topic rather than by category. The skill arm
  moved every history item out with the gist preserved in commit bodies
  and CHANGELOG.md, took the README under 60%, and kept all ten protected
  facts. Turns were level with the baseline (38 against 40).
- **Code: outcome equal, process different.** 13/13 against 12/13, and the
  one separating check is the audit's category coverage. The baseline
  removed the same noise, renamed the same parameters, kept the same
  constraint comments and left the tests green. On a single small file the
  skill's marginal value is the audit and the protected-kept list, not a
  better cleanse; the audit earns its cost when a change is large enough
  to need a reviewer's map.
- **Downstream: modest.** Orienting in the decluttered docs cost the same
  reads as the original and about the same tokens (171k against 167k, the
  baseline's 190k). Adherence was 6/6 in every state: the fixture's facts
  were never hard to find. Decluttering buys tokens per read, not fewer
  reads; fewer reads is `repo-optimization`'s job.
- **Cost of running it.** 1.07x the baseline's tokens; 13 against 9 turns
  on code, level on docs. The extra turns on code are the test runs and
  per-category commits the skill requires.
- **Not measured.** Whether the protected-content rule holds on a repo
  where the signal is subtler than a licence header or a ticket-referenced
  comment; other languages than Python; a repo with real git history to
  check "git holds" against (both fixtures start without one).
