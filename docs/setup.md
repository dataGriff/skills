# Local setup

## Prerequisites

Install [mise](https://mise.jdx.dev/getting-started.html) once:

```bash
curl https://mise.run | sh
```

## Setup

```bash
mise install   # installs the tool versions pinned in mise.toml (task, python)
task setup     # installs the git hooks from .githooks/ and finishes setup
```

That's it. `mise.toml` is the single source of truth for tool versions —
never install `task` or `python` globally for this repo, and never bump a
version outside `mise.toml`.

## Verifying

```bash
task --list    # every available command
task check     # skill best-practice + context-size checks (what CI runs)
```

## Git hooks

`task setup` sets `core.hooksPath` to `.githooks/`, so hooks are versioned
with the repo:

- **pre-commit** → `task pre-commit` (fast checks)
- **pre-push** → `task pre-push` (runs `task ci`, same as GitHub Actions)

Hooks fail with a clear message if `task` isn't installed — run
`mise install` first. Details on the check pipeline: [ci.md](ci.md).
