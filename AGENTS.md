# Agent guide

This repo builds AI agent skills. Keep your context light: this file and the
README are intentionally short. Route via **[docs/index.md](docs/index.md)**
and read only the doc that matches your task.

## Ground rules

1. **Reuse the Taskfile.** Run `task --list` before writing any script or
   one-off command. If a task already does it, use the task. Only add a new
   task when nothing existing covers the need — and add it to `Taskfile.yml`,
   never as a loose script invocation that others can't discover.
2. **Validate before committing.** `task check` runs skill best-practice and
   context-size checks. Git hooks run it automatically (`task setup` installs
   them). CI runs `task ci`.
3. **Skills live in `skills/<name>/SKILL.md`.** Scaffold with
   `task new:skill NAME=my-skill`. Conventions: [docs/skills.md](docs/skills.md).
4. **Keep top-level docs small.** Detail belongs in `docs/` or a skill's
   `references/`, loaded only when needed. Philosophy:
   [docs/docs-style.md](docs/docs-style.md).

## Routing

| Task at hand              | Read                                     |
| ------------------------- | ---------------------------------------- |
| Anything — start here     | [docs/index.md](docs/index.md)           |
| Creating/editing a skill  | [docs/skills.md](docs/skills.md)         |
| Adding/changing tasks     | [docs/tasks.md](docs/tasks.md)           |
| CI, hooks, checks         | [docs/ci.md](docs/ci.md)                 |
