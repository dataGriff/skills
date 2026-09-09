---
name: repo-optimization
description: >-
  Restructure a repository so AI agents work in it efficiently: a tiny
  AGENTS.md (CLAUDE.md = @AGENTS.md) routing to docs/, a Taskfile as the
  single home for scripts, mise-pinned tools, hooks and CI sharing one
  `task ci`, a sandbox bootstrap, and checks that enforce context budgets.
  Use when asked to make a repo agent-ready, AI-friendly, or optimised for
  Claude/AI agents, to set up AGENTS.md or CLAUDE.md, or to centralise
  scripts in a Taskfile.
---

# Repo optimization for AI agents

Transform a repository so agents (and humans) find what they need with
minimal context, reuse existing tooling instead of reinventing it, and get
identical feedback locally and in CI.

Three principles drive every step:

1. **Route early, load late.** Entry files are tiny routers; detail lives
   deep and is loaded only when a task needs it.
2. **One home for scripts.** Every runnable thing is a Taskfile task, so
   agents discover commands with `task --list` instead of re-writing them.
3. **One definition of green.** Hooks, CI, and humans all run the same
   `task ci`.

Be honest about what each principle buys. A small always-loaded layer
mainly improves instruction-following (fewer rules competing for
attention); the token saving is real but modest because the entry file is
prompt-cached across turns. Every routing hop, on the other hand, costs a
tool turn on every task that follows it. Optimise turns as well as tokens.

## Workflow

Work incrementally — each step leaves the repo better even if you stop there.

### 1. Audit and measure what exists

Inventory before touching anything: existing README/CLAUDE.md/AGENTS.md and
their sizes, loose scripts (`scripts/`, `bin/`, `package.json` scripts,
Makefile), doc sprawl, existing CI workflows and hooks, and how tool versions
are pinned. Record the **cold-start cost**: estimated tokens (chars/4) of
everything an agent loads before doing work (CLAUDE.md and its includes,
AGENTS.md, anything the README tells it to read first). You will compare
against this number at the end. Fold existing content into the new
structure — never discard working scripts or docs; relocate them.

### 2. Establish the docs fanout — when it pays

Fanout trades tokens for turns, so size it to the repo:

- **Under ~2000 tokens of agent-relevant docs** (README, CLAUDE.md, and
  anything they tell agents to read, added together): keep one AGENTS.md
  with headed sections, `CLAUDE.md` as `@AGENTS.md`, and no `docs/index.md`
  — however many topics it covers. A single file the agent already has
  beats two Read calls to reach the same content.
- **Above that**: route.
  - Shrink `README.md` to orientation + quick start + a link to
    `docs/index.md`.
  - Create `AGENTS.md`: the agent ground rules (reuse the Taskfile, run the
    checks, where things live) plus a routing table. Keep it under ~60
    lines.
  - Make `CLAUDE.md` contain exactly `@AGENTS.md` — a pure include, so
    there is one agent entrypoint and nothing to drift.
  - Create `docs/index.md` as a routing table: one row per topic doc
    saying *when* to read it. Split detail into focused `docs/<topic>.md`
    files.
- **At most two hops** from AGENTS.md to the detail a task needs
  (AGENTS.md → docs/index.md → topic doc). A doc that only routes onward
  again is a turn spent on nothing; merge it.

Layout details, budgets, and the content-depth rules: read
[references/docs-fanout.md](references/docs-fanout.md) if the repo is big
enough to route.

### 3. Pin tooling with mise, centralise scripts in a Taskfile

- `mise.toml` pins every tool version (at minimum `task`, plus the
  languages the repo uses). It is the only place versions live.
- `Taskfile.yml` absorbs every loose script and command. Migrate Makefile
  targets, package.json scripts, and README shell snippets into named tasks
  with clear `desc:` lines. Use `namespace:action` naming.
- In AGENTS.md, tell agents explicitly: run `task --list` first and reuse
  existing tasks; only add a task when nothing covers the need.
- **Make the Taskfile reachable where agents actually run.** Sandboxes
  (Claude Code on the web, fresh containers, CI without mise) start with
  no mise and no `task`, so rule one of AGENTS.md is unfollowable there
  and the agent falls back to calling scripts directly. Ship
  `scripts/bootstrap.sh` (installs mise, or failing that the pinned `task`
  binary from its GitHub release), wire it into a Claude Code
  `SessionStart` hook, and name it in AGENTS.md as the one script that is
  run directly.

Task design patterns, the bootstrap script, and hook wiring: read
[references/tooling.md](references/tooling.md) if you need more than the
patterns above.

### 4. Wire hooks and CI through the Taskfile

- Versioned hooks in `.githooks/` (activated via
  `git config core.hooksPath .githooks` inside a `task setup`):
  pre-commit → `task pre-commit`, pre-push → `task pre-push` → `task ci`.
- A GitHub Actions workflow that only checks out, installs tools with
  `jdx/mise-action` (reading `mise.toml`), and runs `task ci`. No check
  logic in YAML — if CI-only steps exist, contributors can't reproduce
  failures locally.

### 5. Add automated guardrail checks

Add stdlib-only scripts (invoked via `task check`) that keep the structure
from regressing:

- **Context-size budgets**: line/token limits on README, AGENTS.md,
  docs/index.md and topic docs; `CLAUDE.md == @AGENTS.md` verbatim. Have
  the check *print* the cold-start total every run, not only fail on a
  budget — a cost that is visible gets managed.
- **Convention checks**: whatever the repo's docs promise (doc routing
  rows exist, referenced files exist, every task has a `desc:`; for a
  skills repo, skill frontmatter and progressive-disclosure budgets).

Budgets are constants at the top of each script — changed deliberately, not
worked around. Concrete checks, budget values, and script skeletons: read
[references/checks.md](references/checks.md) only if the repo needs checks
beyond the two above.

### 6. Verify and compare

Run `task ci` yourself before declaring done; where you cannot run
`task`, at least confirm `Taskfile.yml` parses as YAML (quoted `desc:`
lines, quoted `{{ }}` templates, block style) — a Taskfile that fails to
load is worse than the Makefile it replaced. Then measure the agent
experience against the step 1 baseline: starting from AGENTS.md alone, how
many tokens and how many Read calls does it take to learn how to run the
checks, where scripts live, and where detail docs are? The target is under
~1500 tokens and two hops. Report before and after cold-start numbers in
your summary; if the after is not smaller, or needs more hops, the routing
layer is wrong — tighten it or collapse it.

## References

- [references/docs-fanout.md](references/docs-fanout.md) — when fanout
  pays, layout, content-depth rules, budgets for each routing file.
- [references/tooling.md](references/tooling.md) — mise + Taskfile
  patterns, migrating existing scripts, sandbox bootstrap, hook wiring.
- [references/checks.md](references/checks.md) — guardrail check design,
  cold-start report, reusable script skeletons.
