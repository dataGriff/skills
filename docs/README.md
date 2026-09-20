# Docs index

The fallback routing table (a README so it renders in place when you browse `docs/`). `AGENTS.md` carries what most tasks need and
routes the common cases directly; come here when your task is not covered
there. Read only the doc whose trigger matches — each row says when.

## Routes

| When you are…                                              | Do this                                                        |
| ---------------------------------------------------------- | -------------------------------------------------------------- |
| setting up the repo locally, or `task`/mise is missing     | Read [setup.md](setup.md) first — mise, task, hooks, bootstrap |
| creating or editing a skill                                | Read [skills.md](skills.md) before you scaffold or change one  |
| installing these skills into Claude Code, Codex, or Copilot | Read [install.md](install.md) before touching `.claude/` or `.codex/` |
| adding or changing Taskfile tasks, or wondering what exists | Read [tasks.md](tasks.md) before editing `Taskfile.yml`        |
| writing docs or deciding where content should live         | Read [docs-style.md](docs-style.md) first                      |
| working on CI, git hooks, or the check scripts             | Read [ci.md](ci.md) before you change them                     |
