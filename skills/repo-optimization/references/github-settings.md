# GitHub settings: make the host enforce the definition of green

## When this applies

Once CI runs `task ci` (step 6). A check that CI runs but nothing requires
is advisory: a direct push to `main`, a merge with a red check, or a
merge commit that bypasses the squash all land anyway, and the hooks only
catch the contributor who installed them. GitHub enforces it only when
the repo's merge settings and a ruleset on the default branch say so.
Apply this on every repo you own; drift is common, because these settings
are per repo and nothing copies them from one to the next.

## What to set and why

| Setting | Value | Why |
|---|---|---|
| Allow squash merging | on; merge commits and rebase merging off | One commit per PR, so history reads as the PR list and reverts are one commit. |
| Squash commit title and message | PR title, PR body | Deterministic commit message: a conventional-commit PR title becomes the commit, however many commits the branch had. |
| Automatically delete head branches | on | Merged branches never pile up; the branch list is the list of open work. |
| Ruleset on the default branch: restrict deletions, block force pushes | on | `main` cannot be rewritten or removed, by anyone. |
| Ruleset: require linear history | on | Belt and braces for squash-only: nothing can introduce a merge commit. |
| Ruleset: require a pull request | on, 0 approvals, stale reviews dismissed, threads resolved, squash the only allowed method | No direct pushes; every change has a reviewable record. 0 approvals because a solo maintainer cannot approve their own PR; raise it when reviewers exist. |
| Ruleset: require status checks | the CI job that runs `task ci` | Red CI blocks the merge. The context is the job's `name:` (or its id when unnamed), not the workflow name. |
| Bypass actors | none | An admin bypass makes every rule above a suggestion for the people most likely to be in a hurry. |

Use a ruleset, not classic branch protection: rulesets work on free-plan
private repos, apply to the default branch by reference (`~DEFAULT_BRANCH`,
so renaming `main` needs no update), are readable and importable as JSON,
and several can layer (an org-level ruleset plus the repo's own).

## Apply it

Copy or symlink [scripts/github-settings.sh](../scripts/github-settings.sh)
into the target repo's `scripts/` and wrap it in a task so the setting is a
documented, re-runnable step rather than a memory:

```yaml
  setup:github:
    desc: "One-time: squash-only merges, delete head branches, PR + CI required on main: task setup:github [REPO=owner/name] [CHECKS=ci]"
    cmds:
      - "scripts/github-settings.sh --repo {{.REPO | default \"\"}} --checks {{.CHECKS | default \"ci\"}}"
```

The script needs `gh` authenticated with admin rights on the repo. It
patches the merge settings, then creates or updates a ruleset named
`default-branch`; running it again converges on the same state. Flags:
`--checks a,b` for more than one required job, `--checks ""` for a repo
with no CI yet (add the check when CI exists, or the first PR can never
merge), `--approvals N` once there are reviewers, `--dry-run` to print the
requests.

Two things to decide per repo, both left at GitHub's default by the
script:

- **Require branches to be up to date before merging**
  (`strict_required_status_checks_policy`). Off means CI ran on the branch,
  not on the merge result; on means every PR behind `main` must update and
  re-run CI before it can merge. Turn it on where PRs often land
  concurrently in the same files.
- **Auto-merge** (`allow_auto_merge`). Off by default; turn it on when PRs
  wait on slow CI and you want "merge when green".

## Verify

```bash
gh api repos/OWNER/NAME --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge,delete_branch_on_merge}'
gh api repos/OWNER/NAME/rulesets --jq '.[] | {name,enforcement}'
gh api repos/OWNER/NAME/rulesets/ID --jq '[.rules[].type]'
```

Expected: squash true, the other two false, delete true; one active
ruleset whose rules are deletion, non_fast_forward,
required_linear_history, pull_request, required_status_checks. Then prove
it: a direct `git push origin main` is refused, and a PR shows the
required check and only the squash button.

## Caveats

- **Required check names must match exactly.** A job renamed in the
  workflow leaves the ruleset waiting for a check that never reports, and
  every PR blocks. When you rename a job, re-run the script with the new
  `--checks`.
- **A required check on a repo with no CI blocks every merge.** Order:
  CI first, then the ruleset.
- **Org-owned repos** may already carry an org-level ruleset; the repo
  ruleset adds to it and the stricter rule wins. Check
  `gh api repos/OWNER/NAME/rules/branches/main` for the effective set.
- **Classic branch protection** on the same branch keeps applying
  alongside the ruleset. Delete it once the ruleset is active so there is
  one place to read the rules:
  `gh api -X DELETE repos/OWNER/NAME/branches/main/protection`.
- **Agents and the PR requirement.** With no bypass actors, an agent that
  commits to `main` directly gets a refused push. Tell it so in AGENTS.md
  ("always branch and open a PR; `main` only takes squash merges"), which
  turns a failure into the expected workflow.
