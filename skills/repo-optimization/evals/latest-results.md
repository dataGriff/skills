# Eval results: repo-optimization

Last run: 20260920-201340 UTC via `task eval:skills NAME=repo-optimization MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| small-python-repo-from-readme | 16/16 | 5/16 | 51 / 36 | 423.5s / 280.9s | $1.39 / $0.84 |
| fat-claude-md-fits-budget | 10/10 | 8/10 | 12 / 11 | 86.8s / 124.0s | $0.31 / $0.33 |
| already-good-repo-restraint | 10/10 | 8/10 | 11 / 9 | 80.1s / 67.7s | $0.24 / $0.18 |

Grader checks that separated the arms: small-python-repo-from-readme 11/16, fat-claude-md-fits-budget 2/10, already-good-repo-restraint 2/10. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 1.50x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Downstream tasks - the same follow-up jobs run in the fixture repo before the restructure, after the baseline arm's restructure, and after the skill arm's (means per run; adherence = grader checks the answers passed). This is the cost the skill is meant to reduce: what a later agent pays to orient and whether it follows the repo's rules.

| Eval | State | Runs | Adherence | Turns | Reads before first write | Tokens | Cost |
|------|-------|------|-----------|-------|--------------------------|--------|------|
| small-python-repo-from-readme | before | 12 | 27/27 | 7.0 | 4.6 | 192,243 | $0.10 |
| small-python-repo-from-readme | after-baseline | 12 | 27/27 | 7.3 | 4.0 | 256,946 | $0.13 |
| small-python-repo-from-readme | after-skill | 12 | 27/27 | 4.1 | 1.8 | 173,332 | $0.10 |
| fat-claude-md-fits-budget | before | 12 | 31/39 | 2.8 | 0.8 | 124,501 | $0.09 |
| fat-claude-md-fits-budget | after-baseline | 12 | 39/39 | 4.6 | 2.4 | 181,029 | $0.10 |
| fat-claude-md-fits-budget | after-skill | 12 | 39/39 | 3.0 | 0.8 | 135,787 | $0.09 |
| already-good-repo-restraint | before | 6 | 21/21 | 4.3 | 2.3 | 126,981 | $0.07 |
| already-good-repo-restraint | after-baseline | 6 | 21/21 | 4.5 | 2.5 | 126,735 | $0.07 |
| already-good-repo-restraint | after-skill | 6 | 21/21 | 3.0 | 1.0 | 125,552 | $0.07 |

Full outputs (gitignored): `.evals/repo-optimization/20260920-201340/`.

## Notes: restraint fixture and CI wrap rule (2026-09-20, run 201340)

A third fixture tests the case the skill could still degrade: a repo that
is already good (a followed 48-line AGENTS.md, CLAUDE.md as the include,
a Makefile with `make help`, a CI workflow with a matrix, caching, service
containers and a tag-gated deploy job) with one unrouted doc. The correct
output is one route line and NOTES.md. The skill also gained the rule that
an existing workflow with real jobs is wrapped in place, never replaced.

- **It held back.** The skill arm touched AGENTS.md (one explicit route
  to docs/releasing.md) and wrote NOTES.md; no Taskfile, mise, hooks or
  bootstrap; every Makefile target kept; the workflow untouched. 10/10 in
  11 turns and $0.24. The baseline (8/10) also held back but did not add
  the route. Downstream, the routed doc cut the release task from 2.3
  reads and 4.3 turns to 1.0 and 3.0 at equal adherence (the README's
  soft mention was enough to find it eventually; the route makes it
  immediate).
- **The other two fixtures held their results.** README-only: 16/16
  against 5/16, and this run the skill's layout was cheaper than the
  original on every measure (4.1 turns, 1.8 reads, 173k tokens against
  7.0, 4.6, 192k) while the baseline's restructure was dearer than the
  original (7.3, 4.0, 257k). Fat CLAUDE.md: routes only again, 10/10 in
  12 turns and $0.31; downstream 39/39 with the runbook routed against
  31/39 unrouted, where two runs in twelve skipped it; cost level with
  the original (3.0 turns, 0.8 reads, 136k against 2.8, 0.8, 125k).
- **What this does and does not establish.** Across three fixtures and
  one model the skill's outcome was never worse than the original on
  adherence, reads or turns, and on the already-good repo it changed one
  line. Not covered: a workflow where the inline checks have to be
  swapped for `task ci` inside a job that must survive (the fixture's
  workflow already ran `make ci`, so the wrap rule was exercised only as
  "leave it alone"); other models; tasks that edit code.

## Notes: the skill now chooses the least change (2026-09-20, run 194303)

After the run below showed over-treatment, the skill gained a decision
step (routes only / build / fan out), a token-first budget, a tooling
stack conditional on scattered commands, and a verify step that compares
against leaving the repo alone. The fat-CLAUDE.md eval was rewritten to
stop demanding a fanout and grade whether the arm chose the cheaper path.
This run is on the revised skill, 3 downstream repeats.

- **It chose routes only, unprompted.** On the 175-line / 1881-token
  CLAUDE.md the skill arm kept the content as AGENTS.md, made CLAUDE.md
  the include, left RUNBOOK.md in place and added one explicit incident
  route — 16 turns and $0.42 against 52 turns and $1.28 for the previous
  skill's restructure of the same fixture. 10/10 against the baseline's
  8/10 (no include; two facts lost in its rewrite). Running the skill now
  costs 1.07x the baseline's tokens across both fixtures, down from 1.58x.
- **The routed runbook is read every time; the unrouted one is not.**
  Downstream adherence on the fat fixture: 39/39 after the skill, 35/39
  before, where one run in three answered the backlog incident without
  opening RUNBOOK.md. The baseline's restructure also scored 39/39 on
  these tasks but had dropped two facts that no task asked about.
- **Cost matches the original, as it should.** Routes only is the
  original file plus a few lines, so turns (3.0 vs 3.0), reads (0.9 vs
  1.0) and tokens (132k vs 127k) are level with the original; the
  baseline's rewrite is cheaper (0.4 reads, 104k) because it is shorter,
  having lost content. On the README-only fixture, which nothing
  auto-loaded, the skill's build outcome still cuts reads from 4.8 to 2.7
  and turns from 7.1 to 5.2 at 27/27 adherence.
- **Grader fixes this round, all in the skill's disfavour or neutral:**
  routes that wrap across lines are joined before checking; "For
  <situation>, read X" counts as trigger-first; a runbook fact from the
  outage section is no longer demanded of a backlog answer; a file the
  state started with is not a "new file" when a task edits it.
- **Verdict as it stands.** The skill helps where nothing auto-loads
  (fewer reads and turns, rules followed) and where a routed doc was
  unrouted (rules followed instead of skipped one run in three). It no
  longer makes a well-sized entry file worse, because it now leaves it
  alone. It does not reduce tokens for a repo that already fits in one
  auto-loaded file, and it should not be expected to.

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
- **Downstream, 3 repeats, four tasks per fixture including one whose
  facts live only in the runbook or deploy section.** What the skill's
  layout buys a later agent, against the original docs and against the
  baseline's restructure:
  - *Rule adherence.* Skill layout 27/27 and 42/42. Original docs 26/27
    and 37/42: with RUNBOOK.md sitting unrouted beside CLAUDE.md, one run
    in three answered the queue-backlog incident without opening it and
    missed every runbook fact; with the runbook routed ("Before you
    respond to a production incident, read docs/runbook.md") no run
    missed. Baseline restructure 27/27 and 42/42 as well, once the
    grader accepted `make ci` as an entrypoint.
  - *Orientation.* Reads before the first write: README-only fixture 4.4
    (original) → 2.6 (baseline) → 2.3 (skill); fat CLAUDE.md fixture 0.9
    → 3.3 → 1.6. Turns: 6.7 → 6.2 → 4.9 and 2.9 → 5.7 → 4.0. The skill's
    layout is the cheapest restructure on both, and on the README-only
    repo cheaper than the original. On the fat CLAUDE.md repo the
    original wall of text is cheaper to orient in than either
    restructure, because it is auto-loaded and answers everything; the
    skill's layout gives back about half of what the baseline's
    restructure lost.
  - *Tokens and cost.* Per task: 181k → 254k → 204k, and 124k → 205k →
    168k. Totals scale with turns times context, and the restructured
    repo carries a larger auto-loaded AGENTS.md on every turn, so fewer
    reads do not translate into fewer tokens against the original; the
    skill only beats the baseline restructure. Cost is flat at $0.09 to
    $0.12 per task in every state.
  - *Where the skill's layout costs more.* Adding a rule to the notify
    repo took 3.7 reads under the skill's layout against 1.7 in the
    original: with rules split between AGENTS.md and routed docs the agent
    reads several to decide where a new one belongs. Adding a task always
    reads the Taskfile. Those are inherent to a fanned-out repo.
  - *Verdict.* The skill helps on what the routes are for: rules that
    live only in a routed doc get followed, and orientation takes fewer
    reads and turns than any unguided restructure. It does not reduce
    per-task tokens against a repo whose docs are small enough to
    auto-load whole, and it can add a read when placing new content.
    Restructuring a repo that already fits in one auto-loaded file buys
    reliability of routed rules and structure the checks keep, not
    tokens; the earlier single-run token win (85k vs 106k) was noise.

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
