# Eval results: repo-optimization

Last run: 20260909-203052 UTC via `task eval:skills NAME=repo-optimization MODEL=claude-sonnet-5` (commit this file with the skill change so the PR carries the evidence).

Models served: claude-haiku-4-5-20251001, claude-sonnet-5.

| Eval | With skill | Baseline | Turns (skill/base) | Time (skill/base) | Cost (skill/base) |
|------|-----------|----------|--------------------|-------------------|-------------------|
| small-python-repo-from-readme | 13/14 | 6/14 | 48 / 32 | 326.9s / 208.9s | $0.97 / $0.55 |
| fat-claude-md-restructure | 14/14 | 6/14 | 53 / 38 | 326.6s / 221.5s | $1.13 / $0.69 |

Grader checks that separated the arms: small-python-repo-from-readme 7/14, fat-claude-md-restructure 8/14. A check both arms always pass measures nothing; a score delta with none separating is noise.
Token cost, with skill / baseline: 2.10x. Turns above the baseline usually mean SKILL.md loads bundled files unconditionally.

Full outputs (gitignored): `.evals/repo-optimization/20260909-203052/`.

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
