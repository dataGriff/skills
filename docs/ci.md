# CI, hooks, and checks

One principle: **`task ci` is the single definition of "the checks pass."**
Git hooks and GitHub Actions are both thin wrappers around the Taskfile, so
local and remote can never disagree about what gets checked.

```
.githooks/pre-commit ─→ task pre-commit ─→ task check
.githooks/pre-push   ─→ task pre-push   ─→ task ci ─→ task check
.github/workflows/ci.yml ──────────────────→ task ci
```

## The checks

- `task check:skills` (`scripts/check_skills.py`) — skill best practices:
  frontmatter validity, name/directory match, description states capability
  then trigger context, 500-line SKILL.md budget, referenced files exist,
  no orphaned bundled files, reference-doc links resolve, ToCs on large
  references, and (warning) SKILL.md phrasing that loads a bundled file on
  every use — see the cost-discipline rules in [skills.md](skills.md).
- `task check:context` (`scripts/check_context.py`) — context-size budgets:
  README/AGENTS/docs/index line+token limits, `CLAUDE.md == @AGENTS.md`,
  topic doc size, SKILL.md token budget.

Both scripts are stdlib-only python; budgets are constants at the top of
each script. Change a budget deliberately, in the script, with a reason in
the commit message — not by working around a failing check.

## Adding a CI step

Add it to the `ci` task chain in `Taskfile.yml`. The GitHub workflow
(`.github/workflows/ci.yml`) installs tools with `jdx/mise-action` (reading
`mise.toml`) and runs `task ci` — it should never grow check logic of its
own, because anything only CI runs is something contributors can't run
locally.

## Eval evidence on pull requests

Skill changes carry their eval evidence in the diff
(`evals/latest-results.md`, see [skills.md](skills.md)) — but reviewers
read the PR, not the file tree. Two mechanisms keep the summary visible in
the PR itself:

- `.github/pull_request_template.md` asks the author to paste the results
  table (or say why no re-run was needed).
- The `eval-summary` CI job runs `task pr:eval-summary` on every PR and
  upserts the output as a sticky comment: each changed skill's
  `latest-results.md`, with a ⚠️ when the skill changed without a refreshed
  results file or defines no evals. The summarising logic lives in
  `scripts/pr_eval_summary.py` behind the task (runnable locally); the
  workflow step only posts the output — delivery glue, not check logic.

## Hooks

Versioned in `.githooks/`, activated by `task setup` (sets
`core.hooksPath`). They intentionally hard-fail when `task` is missing
rather than silently skipping checks. Bypass in an emergency with
`git commit --no-verify` — CI will still catch you.
