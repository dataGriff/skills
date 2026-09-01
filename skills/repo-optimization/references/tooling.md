# mise + Taskfile + hooks: patterns

## mise.toml

Pin exact-enough versions of every tool the repo needs; `task` is always
one of them:

```toml
[tools]
task = "3.44"
python = "3.12"
# node = "22", go = "1.23", ... whatever the repo uses
```

CI installs from the same file via `jdx/mise-action@v2`, so local and CI
tool versions cannot diverge. Never document a global install of a pinned
tool.

## Taskfile.yml patterns

```yaml
version: "3"
tasks:
  default:            # `task` alone lists everything — discoverability
    silent: true
    cmds: [task --list]

  setup:              # one command from clone to working
    cmds:
      - task: hooks:install

  hooks:install:
    cmds:
      - git config core.hooksPath .githooks
      - chmod +x .githooks/*
    status:           # idempotent — safe to re-run
      - test "$(git config core.hooksPath)" = ".githooks"

  check:              # aggregate; hooks and ci compose from here
    cmds:
      - task: check:conventions
      - task: check:context

  pre-commit: {cmds: [{task: check}]}       # hook entrypoints
  pre-push:   {cmds: [{task: ci}]}
  ci:         {cmds: [{task: check}]}       # THE definition of green
```

Conventions:

- `namespace:action` names; every task has a `desc:` written for someone
  who has never seen it (`task --list` is the discovery UI).
- Non-trivial logic goes in `scripts/*.py` (stdlib-only where possible),
  always invoked through a task — the task name is the stable interface.
- Tell agents in AGENTS.md: `task --list` before writing anything; extend
  an existing task rather than duplicating; never call scripts directly.

## Migrating existing scripts

Absorb, don't delete: Makefile targets, `package.json` scripts, README
shell snippets, and loose `bin/` scripts each become a task (possibly just
wrapping the original command). Leave a Makefile shim only if external
systems call it (`make test: ; task test`).

## Git hooks

Versioned in `.githooks/`, activated by `task setup`. Each hook is a tiny
delegator:

```bash
#!/usr/bin/env bash
set -euo pipefail
if ! command -v task >/dev/null 2>&1; then
  echo "pre-commit: 'task' not found — run 'mise install' first." >&2
  exit 1
fi
exec task pre-commit
```

Hard-fail when `task` is missing (a silently skipped hook is worse than a
noisy one). pre-commit runs fast checks; pre-push runs the full `task ci`
so a push that passes locally passes remotely.

## GitHub Actions

The workflow stays a thin wrapper — checkout, mise-action, `task ci`:

```yaml
name: CI
on: {push: {branches: [main]}, pull_request: {}}
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: jdx/mise-action@v2
      - run: task ci
```

New checks are added to the `ci` task, never to the YAML. Anything only CI
can run is a failure contributors cannot reproduce.
