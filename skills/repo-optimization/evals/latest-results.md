# Eval results: repo-optimization

Last run: 20260920-185310 UTC via `task eval:skills NAME=repo-optimization MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| small-python-repo-from-readme | 15/16 | 7/16 | 59 / 33 | 357.8s / 255.1s | $1.25 / $0.64 |
| fat-claude-md-restructure | 16/16 | 7/16 | 52 / 40 | 397.6s / 282.2s | $1.28 / $0.99 |

Grader checks that separated the arms: small-python-repo-from-readme 8/16, fat-claude-md-restructure 9/16. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.58x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Downstream tasks - the same follow-up jobs run in the fixture repo before the restructure, after the baseline arm's restructure, and after the skill arm's (means per run; adherence = grader checks the answers passed). This is the cost the skill is meant to reduce: what a later agent pays to orient and whether it follows the repo's rules.

| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |
|------|-------|------|-----------|-------|--------------------------|--------|------|
| small-python-repo-from-readme | before | 3 | 5/5 | 7.0 | 4.7 | 185,246 | $0.10 |
| small-python-repo-from-readme | after-baseline | 3 | 4/5 | 5.0 | 2.0 | 214,347 | $0.11 |
| small-python-repo-from-readme | after-skill | 3 | 5/5 | 4.3 | 1.0 | 196,700 | $0.10 |
| fat-claude-md-restructure | before | 3 | 9/9 | 2.3 | 0.3 | 105,527 | $0.08 |
| fat-claude-md-restructure | after-baseline | 3 | 9/9 | 6.0 | 3.3 | 234,439 | $0.11 |
| fat-claude-md-restructure | after-skill | 3 | 9/9 | 2.0 | 0.0 | 85,343 | $0.06 |

Full outputs (gitignored): `.evals/repo-optimization/20260920-185310/`.

## Notes: AGENTS.md-first, explicit routes, downstream evals (2026-09-20)

The skill changed from "tiny router AGENTS.md, everything behind a
docs/index.md hop" to "AGENTS.md carries what most tasks need within
~150 lines / ~2000 tokens, routes the rest with 'before you X, read
docs/Y' instructions, docs/README.md as the fallback index". Three things
this run established:

- **The first run of the new skill was contaminated.** Both arms scored
  15/16 with zero separating checks. The baseline's NOTES.md repeated
  phrases from this repo's own AGENTS.md: `claude -p` loads CLAUDE.md from
  every ancestor of its working directory, and eval sessions ran under
  `.evals/`, inside this repo. The richer AGENTS.md leaked the whole recipe
  to the baseline. Arms now run in a scratch directory outside the repo;
  the table above is the clean rerun. Earlier runs (2026-09-09) were
  exposed to the same leak with a smaller AGENTS.md, so their baseline
  numbers are optimistic too.
- **Clean numbers.** With the skill 15/16 and 16/16 against 7/16 for the
  baseline, with 8 and 9 checks separating the arms. The skill arm's one
  miss on the small fixture is a genuine soft route: it wrote "(see
  docs/migrations.md)" with no explicit route to that doc, despite the
  rule. Every other route it wrote was a "Before you ..., read docs/..."
  line, though as bare paths rather than links; the grader now accepts
  either, and the skill text asks for links.
- **Downstream: the restructured repo is cheaper to work in, and a naive
  restructure is dearer than the wall of text it replaced.** The same
  three follow-up tasks per fixture, one run each (so treat single-run
  differences as indicative):
  - Small Python repo: reads before the first write fell from 4.7 (README
    only, which nothing auto-loads) to 2.0 after the baseline restructure
    and 1.0 after the skill's; turns from 7.0 to 5.0 to 4.3. Adherence 5/5
    before and after the skill, 4/5 after the baseline.
  - Fat CLAUDE.md service: the original already costs 0.3 reads and 2.3
    turns, because a 2000-token CLAUDE.md is auto-loaded and answers
    everything. The baseline restructure hid the rules behind docs and
    made later work *worse*: 3.3 reads, 6.0 turns, 234k tokens. The
    skill's AGENTS.md-first layout kept it at 0.0 reads and 2.0 turns at
    85k tokens, below the original's 106k. That is the case for carrying
    the common case in AGENTS.md rather than routing it.
  - Token totals include the CLI's cached system prompt (about 85k per run
    is the floor for a single-write task), so the repo-specific saving is
    larger than the ratios suggest. Adherence separated nothing on the
    notify fixture (9/9 in every state): those tasks need harder rules, or
    2-3 repeats, before adherence can carry a decision.

## Notes: first evals and what they changed (2026-09-09)

This skill had no evals before this run. Two fixtures: a small Python
service documented only by a README plus Makefile/package.json/deploy.sh
(under the fanout threshold, so the right answer is one AGENTS.md and no
docs/index.md), and a service with a ~2000-token CLAUDE.md that must be
split into a routed layout without losing a rule.

- **The first run (20260909-200034) found a real defect.** Both with-skill
  Taskfiles failed to parse: an unquoted `desc:` containing a colon, and
  `cmds: [pnpm test -- {{.CLI_ARGS}}]` in flow style. The reference
  skeleton used flow style and unquoted descs, so the skill was inviting
  it. Scores were 11/14 vs 9/14 and 12/14 vs 13/14 — the skill losing on
  the second fixture because a Taskfile `task` cannot load is worse than
  the pnpm scripts it replaced. The skeleton is now block style with
  quoted descs, the trap list is in tooling.md, and the verify step asks
  for a YAML parse when `task` cannot be run. The same run also showed the
  fanout threshold being ignored (an index for an 886-token README); the
  wording now makes size the only trigger. The rerun above is on the
  corrected skill.
- **Where the delta comes from.** The separating checks are the Taskfile
  parsing and carrying a `ci` task, `task --list` in AGENTS.md, mise pins,
  both hooks, a thin CI workflow, and the sandbox bootstrap. The baseline
  is not bad at the docs part: it reliably produces `CLAUDE.md ==
  @AGENTS.md`, a small AGENTS.md, and preserves the original rules. What
  it does not do without the skill is pick this tooling stack — across the
  two runs its baseline scores ranged 6–13/14 because it sometimes chose
  a Taskfile and sometimes did not. The grader measures conformance to
  these conventions, not the only valid design.
- **Cost.** With the skill, 48–53 turns against 32–38 and ~2.1× the
  tokens. Around four turns are the reference and bootstrap loads; the
  rest is the extra work the skill asks for (hooks, bootstrap, guardrail
  check scripts, before/after numbers) that the baseline simply does not
  produce. This is a once-per-repository task, so the ~$0.45 premium buys
  a structure the checks then keep in place; it is not a per-prompt cost.
- **Not measured here.** Whether the resulting repo actually makes later
  agent tasks cheaper. That needs a second-stage eval: run a task in the
  before and after repos and compare turns and tokens. The cold-start
  numbers each arm reports in NOTES.md (886 → ~600 tokens; 2067 → ~750–1150)
  are the proxy until then.
