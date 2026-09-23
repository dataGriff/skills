# skills

A repository for creating and maintaining AI agent skills. One canonical
copy per skill works in Claude Code, Codex, and GitHub Copilot — in-repo via
committed symlinks, everywhere else via `task install:skills`, and for
Claude Code alone via `/plugin marketplace add dataGriff/skills`
([docs/install.md](docs/install.md)).

**Start here → [docs/README.md](docs/README.md)**

The repo skills (`repo-optimization`, `repo-declutter`,
`repo-consistency-checker`, `orwell-prose`) implement the
[Codebase Interface](https://codebaseinterface.org) spec and are moving to
`codebase-interface/skills`; until that repo exists they are canonical here.

Quick start:

```bash
mise install   # install pinned tools (task, python)
task setup     # install git hooks + verify environment
task --list    # see every available command
```

No mise (sandbox, fresh container)? `scripts/bootstrap.sh` installs `task`.

Everything runnable lives in the [Taskfile](Taskfile.yml). For agents,
[AGENTS.md](AGENTS.md) carries what most tasks need and routes the rest to
[docs/](docs/README.md) — read only what the task at hand needs.
