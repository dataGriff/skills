# Parallel delivery with git worktrees

Git worktrees give each in-flight unit its own working directory sharing
one repository, so parallel units never fight over a single checkout —
no stashing, no half-finished state bleeding between branches, and
multiple agents or humans can build and test simultaneously.

Use worktrees only for units with **no dependency between them** (see the
breakdown's depends-on column). Parallelizing dependent units just moves
the integration pain to merge time.

## Setup

From the main checkout, one worktree per unit, as a sibling of the repo:

```bash
git worktree add -b <branch-name> ../<repo>-<unit-slug> origin/main
```

- Branch from `origin/main` (or the repo's default branch), not from the
  current checkout — parallel units must not accidentally stack.
- Name the directory after the unit and, when tracked in Linear, use the
  issue's branch-name format for the branch
  (`username/abc-123-accept-currency-code`), so directory ↔ branch ↔
  issue map one-to-one.
- `git worktree list` shows what's in flight; treat it as the live view
  of parallel delivery.

Each worktree needs its own copies of anything gitignored that the build
requires: install dependencies per worktree, copy `.env`-style local
config from the main checkout, and give long-running dev servers distinct
ports. A repo-provided setup task (check `task --list`, `make help`, or
package scripts) beats doing this by hand.

## Working in parallel

- **One unit per worktree, one PR per worktree.** A worktree is delivery
  isolation for its unit, not a second workspace to accumulate changes in.
- Commits, branches, and the object store are shared instantly across
  worktrees (no pushing needed to see another worktree's commits), but a
  branch checked out in one worktree can't be checked out in another —
  that constraint is a feature: it prevents two parallel efforts from
  silently sharing a branch.
- When dispatching parallel units to agents (subagents, or separate
  Claude sessions), give each agent exactly one worktree and its unit's
  scope — including the unit's out-of-scope list — and have each produce
  its own PR. Review and merge PRs one at a time; after each merge,
  rebase or merge `origin/main` into the remaining worktrees' branches so
  each stays a small clean diff against an up-to-date base.

## Cleanup

A merged unit's worktree is finished inventory — remove it promptly:

```bash
git worktree remove ../<repo>-<unit-slug>
git branch -d <branch-name>          # after merge
git worktree prune                    # if a directory was deleted manually
```

Stale worktrees pin their branches and confuse "what's in flight", so
cleanup after each merge is part of delivering the unit, not optional
housekeeping.

## When not to bother

Worktrees pay off for genuinely concurrent units. For strictly sequential
delivery — finish a unit, merge, start the next — a single checkout with
one branch at a time is simpler; don't add worktree overhead the plan
doesn't need.
