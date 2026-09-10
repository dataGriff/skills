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
    desc: "List all available tasks"
    silent: true
    cmds:
      - task --list

  setup:              # one command from clone to working
    desc: "One-time setup: install git hooks"
    cmds:
      - task: hooks:install

  hooks:install:
    desc: "Point git at the versioned hooks in .githooks/"
    cmds:
      - git config core.hooksPath .githooks
      - chmod +x .githooks/*
    status:           # idempotent — safe to re-run
      - test "$(git config core.hooksPath)" = ".githooks"

  test:
    desc: "Run the tests; pass a path to run one file: task test -- path"
    cmds:
      - "pytest {{.CLI_ARGS}}"

  check:              # aggregate; hooks and ci compose from here
    desc: "Run every check (what the hooks and CI run)"
    cmds:
      - task: check:conventions
      - task: check:context

  pre-commit:         # hook entrypoints
    desc: "Fast checks run by the pre-commit hook"
    cmds:
      - task: check
  pre-push:
    desc: "Full checks run by the pre-push hook"
    cmds:
      - task: ci
  ci:                 # THE definition of green
    desc: "Everything CI runs"
    cmds:
      - task: check
```

YAML traps that silently produce a Taskfile `task` refuses to load — both
seen in eval runs, and worse than the Makefile they replaced:

- A `desc:` containing a colon (`desc: Check docs: routes exist`) is a
  YAML error. Quote every `desc:`.
- A command containing `{{ }}` templates (`{{.CLI_ARGS}}`, `{{.PYTHON}}`)
  must be quoted, and never sit inside flow style (`cmds: [ ... ]`).
  Prefer block style throughout; it has no such edge cases.
- If you cannot run `task` where you are working, at least parse the file
  with any YAML parser you already have. For example, with PyYAML installed:
  `python3 -c 'import yaml,sys; yaml.safe_load(open("Taskfile.yml"))'`.

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

## Sandboxes: bootstrap `task` where mise is absent

Claude Code on the web, fresh containers, and CI runners without
`mise-action` have neither mise nor `task`, so "run `task --list` first"
cannot be followed and hooks that hard-fail on a missing `task` block every
commit. Ship a bootstrap that closes the gap and is the one script allowed
to be run directly.

Copy [scripts/bootstrap.sh](../scripts/bootstrap.sh) from this skill into
the target repo's `scripts/` unchanged. It is idempotent and tries, in
order: `task` already present; `mise install` if mise is present; the mise
installer; and finally the `task` version pinned in `mise.toml`, downloaded
from its GitHub release (installer hosts are often blocked by egress
policies while GitHub is allowed). When run as a Claude Code hook it
persists PATH through `$CLAUDE_ENV_FILE`.


Wire it into Claude Code on the web with a SessionStart hook in
`.claude/settings.json` pointing at `.claude/hooks/session-start.sh`, which
exits early unless `CLAUDE_CODE_REMOTE=true` and otherwise execs the
bootstrap. Name the script in AGENTS.md: "if `task` is missing, run
`scripts/bootstrap.sh` once". Test the fallback path with the mise host
blocked — egress policies commonly block it while allowing GitHub.

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
