# Taskfile conventions

`Taskfile.yml` is the single home for everything runnable in this repo.
If it can be run, it is a task; scripts in `scripts/` exist only as the
implementation behind a task and are always invoked *through* one.

## Reuse before you write

Run `task --list` first. If a task already does what you need — or nearly
does — use it or extend it. Do **not**:

- write a one-off shell pipeline that duplicates an existing task,
- add a new script that overlaps an existing one,
- invoke `scripts/*.py` directly (the task is the stable interface).

Duplicated logic drifts: the hook version passes while the CI version fails,
and nobody notices until a broken push. One task, called from everywhere,
cannot drift.

## Adding a task

Only when nothing existing covers the need:

1. Add it to `Taskfile.yml` with a clear `desc:` (that's what `task --list`
   shows — write it for someone who has never seen the task).
2. Use `namespace:action` naming (`check:skills`, `hooks:install`,
   `new:skill`).
3. Non-trivial logic goes in a python script under `scripts/` (stdlib only —
   no dependency management needed), called by the task.
4. If CI should run it, add it to the `ci` task's chain — never add steps
   directly to the GitHub workflow (see [ci.md](ci.md)).

## Current entrypoints

`task --list` is authoritative; the important chains are:

- `setup` → `hooks:install`
- `check` → `check:skills` + `check:context`
- `eval:skills` → with/without-skill effectiveness evals (on demand, not CI)
- `pre-commit` / `pre-push` → hook entrypoints
- `ci` → everything GitHub Actions runs
