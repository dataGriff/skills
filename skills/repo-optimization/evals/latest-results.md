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
| small-python-repo-from-readme | before | 12 | 26/27 | 6.7 | 4.4 | 180,742 | $0.09 |
| small-python-repo-from-readme | after-baseline | 12 | 27/27 | 6.2 | 2.6 | 253,660 | $0.12 |
| small-python-repo-from-readme | after-skill | 12 | 27/27 | 4.9 | 2.3 | 204,242 | $0.10 |
| fat-claude-md-restructure | before | 12 | 37/42 | 2.9 | 0.9 | 124,380 | $0.09 |
| fat-claude-md-restructure | after-baseline | 12 | 42/42 | 5.7 | 3.3 | 205,065 | $0.11 |
| fat-claude-md-restructure | after-skill | 12 | 42/42 | 4.0 | 1.6 | 167,885 | $0.09 |

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
