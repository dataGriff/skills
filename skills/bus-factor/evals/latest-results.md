# Eval results: bus-factor

Last run: 20261015-052730 UTC via `task eval:skills NAME=bus-factor MODEL=claude-sonnet-5-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-5-5, claude-sonnet-5-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| dave-knows-everything | 19/19 | 16/19 | 10 / 17 | 59.7s / 71.6s | $0.20 / $0.22 |
| dave-is-leaving | 13/13 | 9/13 | 10 / 5 | 95.9s / 56.1s | $0.30 / $0.16 |

Grader checks that separated the arms: dave-knows-everything 3/19, dave-is-leaving 4/13. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.39x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Downstream tasks - the same follow-up jobs run in the fixture repo before the restructure, after the baseline arm's restructure, and after the skill arm's (means per run; adherence = grader checks the answers passed). This is the cost the skill is meant to reduce: what a later agent pays to orient and whether it follows the repo's rules.

| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |
|------|-------|------|-----------|-------|--------------------------|--------|------|
| dave-knows-everything | before | 2 | 12/12 | 8.5 | 6.5 | 191,448 | $0.10 |
| dave-knows-everything | after-baseline | 2 | 12/12 | 5.0 | 3.0 | 199,685 | $0.11 |
| dave-knows-everything | after-skill | 2 | 12/12 | 4.0 | 3.0 | 157,932 | $0.10 |

Full outputs (gitignored): `.evals/bus-factor/20261015-052730/`.

## Notes: first evals (2026-10-15)

One fixture, two prompts. `invoicer` is a small Python service whose
setup, deploys and odd constants sit with one maintainer (Dave): the
README routes the `.env` and deploys through him, `deploy.sh` hard-codes
his home directory, four env vars are read in code and documented
nowhere, and `make_history.sh` rebuilds a history in which two "why"s are
recoverable from commit messages (FIN-212 half-even rounding, the 300
req/min rate limit behind `BATCH_SIZE`) and one is not (`RETRY_LIMIT`
3 → 7, "bump retries").

- **Fix task: both arms did real work; the skill's structure separates
  them.** 19/19 against 16/19. Both arms wrote `.env.example`, fixed
  `deploy.sh`, and moved the history-backed reasons into the repo. The
  baseline produced a five-row summary with no per-stage walk and noted
  the retry bump as "unexplained" without putting it to anyone. The skill
  arm scored every newcomer stage before and after, marked each finding's
  source as repo or person, proposed `CODEOWNERS` without writing it, and
  closed with a question list per maintainer. It took fewer turns (10
  against 17).
- **Handover task: the skill earns its cost.** 13/13 against 9/13. The
  baseline's five questions missed deploy access, AWS/SSM permissions and
  who else can deploy. The skill arm mined history first, so it did not
  ask Dave what commits already answer, and it asked him 16 specific
  questions. It also cost twice the turns (10 against 5), mostly the scan
  and `git log` calls.
- **Grader fixes before this summary.** The first grading had three false
  negatives on the skill arm: a path left in a `# was …` comment, env vars
  listed in `.env.example` rather than the report, and an ownership
  question about FIN-212 counted as a "why" question. A baseline doc at
  `docs/KNOWLEDGE.md` was also taken for a report. All four were fixed in
  `grade.py` and both arms were regraded.
- **Downstream: cheaper orientation, same answers.** A newcomer agent
  answered all five questions correctly in every state, so adherence does
  not separate. That is partly a fixture leak: the `before` state ships
  `make_history.sh`, whose text holds the commit messages. After the
  skill arm's changes the newcomer took 4 turns and 158k tokens, against
  5 turns and 200k after the baseline and 8.5 turns and 191k before.
- **Not measured.** Repos with real multi-author history, where
  concentration is less obvious; languages other than Python; whether
  `CODEOWNERS` proposals hold up once a human confirms them.
