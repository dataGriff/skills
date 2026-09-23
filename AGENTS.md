# Agent guide

This repo builds AI agent skills (`skills/<name>/SKILL.md`). This file
carries what most tasks need; `CLAUDE.md` is `@AGENTS.md`. Open a routed
doc only when its trigger in the Routes table fires.

## Ground rules

1. **Reuse the Taskfile.** Run `task --list` before writing any script or
   one-off command. If a task already does it, use the task. Add a new
   task only when nothing existing covers the need, and add it to
   `Taskfile.yml` — never as a loose script others can't discover. Never
   invoke `scripts/*.py` directly; the task is the stable interface.
2. **Validate before committing.** `task check` runs the skill
   best-practice and context-size checks. Git hooks run it automatically
   (`task setup` installs them). CI runs `task ci`, the single definition
   of green; the GitHub workflow is a thin wrapper and never grows checks.
3. **No `task`?** Sandboxes and fresh containers start without mise. Run
   `scripts/bootstrap.sh` once — the one script meant to be run directly.
   Tool versions live only in `mise.toml`; never install or bump elsewhere.
4. **Budgets are the feature.** When a check fails, move content deeper
   (into `docs/` or a skill's `references/`); never raise the budget.

## Commands

| Command                                      | Does                                                        |
| -------------------------------------------- | ----------------------------------------------------------- |
| `task setup`                                 | one-time: install the versioned git hooks                   |
| `task check`                                 | `check:skills` + `check:context` + `check:cbi` — hooks and CI |
| `task new:skill NAME=my-skill`               | scaffold `skills/my-skill/`                                 |
| `task eval:skills NAME=x [MODEL=...]`        | with/without-skill evals via the `claude` CLI (not in CI)   |
| `task install:skills [AGENTS=..] [SKILLS=..]`| symlink skills into `~/.claude`, `~/.codex`, `~/.copilot`   |
| `task ci`                                    | everything GitHub Actions runs                              |

## Layout

```
AGENTS.md        this file (CLAUDE.md is @AGENTS.md)
Taskfile.yml     every runnable script — `task --list`
mise.toml        pinned tool versions
skills/<name>/   SKILL.md + references/ scripts/ assets/ evals/
docs/            topic docs, routed from here and from docs/README.md
scripts/         python behind the tasks (stdlib only; run via task)
.githooks/       pre-commit → task check, pre-push → task ci
.github/         CI workflow: mise-action + `task ci`; eval-summary PR comment
.claude/ .codex/ symlinks into skills/, plus the SessionStart bootstrap hook
```

## Skill conventions

The rules that every skill change must meet; `docs/skills.md` holds the
reasoning, examples and eval workflow.

- **Frontmatter**: `name` is lowercase-hyphenated and equals the directory
  name. `description` (≤1024 chars) states the capability first, then
  explicit triggers ("Use when the user…"); it is the only triggering
  mechanism, so be a little pushy. Descriptions load into every
  conversation, and `task check:context` budgets the suite-wide total.
- **SKILL.md** ≤500 lines / ~5000 tokens. Imperative voice; explain why a
  rule matters rather than stacking MUSTs; generalise beyond one example.
- **References are opt-in.** Every pointer to `references/`, `scripts/` or
  `assets/` states a condition ("read X when …"). Unconditional loads
  ("start from the template", a read inside a numbered step with no
  condition) cost a tool turn on every use; `task check:skills` warns.
- **Every bundled file is mentioned** in SKILL.md or a reference doc;
  reference files over 300 lines get a table of contents.
- **Evals**: when you create a skill or meaningfully edit one (workflow,
  guidance, references), run `task eval:skills NAME=<skill>` and commit
  the refreshed `evals/latest-results.md`. The PR template asks for the
  table; CI posts it as a sticky comment. Typo fixes need no re-run.

## Docs conventions

- **Content depth**: needed by most tasks → this file; by one kind of
  task → `docs/<topic>.md`; by one skill → its `references/`; by nobody →
  delete it.
- **Every doc has an explicit route**: trigger, then "read", then the
  file. "See docs/x.md" is not a route. `task check:context` fails on a
  soft route or an unrouted doc.
- **Budgets** (`task check:context`): README ≤60 lines, this file ≤150
  lines / ~2000 tokens, `docs/README.md` ≤100, topic docs ≤300.

## Routes — read before you act

| When you are…                                  | Do this                                                              |
| ---------------------------------------------- | -------------------------------------------------------------------- |
| creating or editing a skill                    | Read [docs/skills.md](docs/skills.md) first — anatomy, cost discipline, evals |
| adding or changing a Taskfile task             | Read [docs/tasks.md](docs/tasks.md) before editing `Taskfile.yml`    |
| changing CI, git hooks, or the check scripts   | Read [docs/ci.md](docs/ci.md) before you change them                 |
| writing docs or deciding where content lives   | Read [docs/docs-style.md](docs/docs-style.md) first                  |
| doing any task not covered above               | Read [docs/README.md](docs/README.md) before you start; do not guess a convention |
