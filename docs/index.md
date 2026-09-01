# Docs index

Single routing point for this repo's documentation. README.md and AGENTS.md
point here; this page points onward. Read only the doc your current task
needs — that is the whole point of the fanout style.

## What this repo is

A workspace for building AI agent skills (`skills/<name>/SKILL.md`), with
tooling pinned by [mise](https://mise.jdx.dev), all scripts centralised in a
[Taskfile](https://taskfile.dev), git hooks and CI that share one `task ci`
entrypoint, and automated checks for skill quality and context size.

## Routes

| Doc                            | Read it when you are…                                      |
| ------------------------------ | ---------------------------------------------------------- |
| [setup.md](setup.md)           | setting up the repo locally (mise, task, hooks)            |
| [skills.md](skills.md)         | creating or editing a skill; skill best practices          |
| [tasks.md](tasks.md)           | adding or changing Taskfile tasks; wondering what exists   |
| [docs-style.md](docs-style.md) | writing docs; deciding where content should live           |
| [ci.md](ci.md)                 | working on CI, git hooks, or the check scripts             |

## Layout

```
AGENTS.md        agent entrypoint (CLAUDE.md is @AGENTS.md)
Taskfile.yml     every runnable script — `task --list`
mise.toml        pinned tool versions
skills/          one directory per skill
docs/            this fanout
scripts/         python behind the check/scaffold tasks (run via task)
.githooks/       versioned git hooks (installed by `task setup`)
.github/         CI workflow — a thin wrapper over `task ci`
```
