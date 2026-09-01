---
name: repo-optimization
description: >-
  Optimize a codebase so AI agents can work in it efficiently: fanout docs
  (README/AGENTS.md routing to docs/index.md), CLAUDE.md as @AGENTS.md, mise
  for pinned tooling, a Taskfile as the single home for all scripts, git
  hooks and a GitHub Action that share one `task ci` entrypoint, and
  automated checks for context size and conventions. Use when the user asks
  to make a repo "agent-ready", "AI-friendly", or "optimized for Claude/AI
  agents", to set up AGENTS.md or CLAUDE.md, to restructure docs so agents
  don't load too much context, to centralise scripts in a Taskfile, or to
  set up a new repo following this repository's conventions.
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

## Workflow

Work incrementally — each step leaves the repo better even if you stop there.

### 1. Audit what exists

Inventory before touching anything: existing README/CLAUDE.md/AGENTS.md and
their sizes, loose scripts (`scripts/`, `bin/`, `package.json` scripts,
Makefile), doc sprawl, existing CI workflows and hooks, and how tool versions
are pinned. Fold existing content into the new structure — never discard
working scripts or docs; relocate them.

### 2. Establish the docs fanout

- Shrink `README.md` to orientation + quick start + a link to
  `docs/index.md`.
- Create `AGENTS.md`: the agent ground rules (reuse the Taskfile, run the
  checks, where things live) plus a routing table. Keep it under ~60 lines.
- Make `CLAUDE.md` contain exactly `@AGENTS.md` — a pure include, so there
  is one agent entrypoint and nothing to drift.
- Create `docs/index.md` as a routing table: one row per topic doc saying
  *when* to read it. Split detail into focused `docs/<topic>.md` files.

Layout details and content-depth rules: read
[references/docs-fanout.md](references/docs-fanout.md) when doing this step.

### 3. Pin tooling with mise, centralise scripts in a Taskfile

- `mise.toml` pins every tool version (at minimum `task`, plus the
  languages the repo uses). It is the only place versions live.
- `Taskfile.yml` absorbs every loose script and command. Migrate Makefile
  targets, package.json scripts, and README shell snippets into named tasks
  with clear `desc:` lines. Use `namespace:action` naming.
- In AGENTS.md, tell agents explicitly: run `task --list` first and reuse
  existing tasks; only add a task when nothing covers the need.

Task design patterns and migration guidance: read
[references/tooling.md](references/tooling.md) when doing this step.

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
  docs/index.md and topic docs; `CLAUDE.md == @AGENTS.md` verbatim.
- **Convention checks**: for a skills repo, skill frontmatter and
  progressive-disclosure budgets; otherwise whatever conventions the repo
  declares (doc routing rows exist, referenced files exist, etc.).

Budgets are constants at the top of each script — changed deliberately, not
worked around. Concrete checks, budget values, and script skeletons: read
[references/checks.md](references/checks.md) when doing this step.

### 6. Verify

Run `task ci` yourself before declaring done. Then sanity-check the agent
experience: starting from AGENTS.md alone, can you find how to run checks,
where scripts live, and where detail docs are — loading fewer than ~1500
tokens? If not, tighten the routing layer.

## References

- [references/docs-fanout.md](references/docs-fanout.md) — fanout layout,
  content-depth rules, budgets for each routing file.
- [references/tooling.md](references/tooling.md) — mise + Taskfile patterns,
  migrating existing scripts, hook wiring.
- [references/checks.md](references/checks.md) — guardrail check design and
  reusable script skeletons.
