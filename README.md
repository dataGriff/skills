# skills

A repository for creating and maintaining AI agent skills. One canonical
copy per skill works in Claude Code, Codex, and GitHub Copilot — in-repo via
committed symlinks, everywhere else via `task install:skills`
([docs/install.md](docs/install.md)).

**Start here → [docs/index.md](docs/index.md)**

Quick start:

```bash
mise install   # install pinned tools (task, python)
task setup     # install git hooks + verify environment
task --list    # see every available command
```

Everything runnable lives in the [Taskfile](Taskfile.yml). Docs are
deliberately thin at the top and fan out from [docs/index.md](docs/index.md) —
read only what the task at hand needs.
