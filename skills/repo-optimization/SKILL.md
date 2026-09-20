---
name: repo-optimization
description: >-
  Restructure a repository so AI agents work in it efficiently: an
  AGENTS.md (CLAUDE.md = @AGENTS.md) that carries what most tasks need
  within a hard budget, explicit "before you X, read docs/Y" routes for the
  rest, a docs/index.md only when the routed docs outgrow AGENTS.md, a
  Taskfile as the single home for scripts, mise-pinned tools, hooks and CI
  sharing one `task ci`, a sandbox bootstrap, and checks that enforce the
  budgets. Use when asked to make a repo agent-ready, AI-friendly, or
  optimised for Claude/AI agents, to set up or slim AGENTS.md or CLAUDE.md,
  to decide what belongs in AGENTS.md versus docs/, or to centralise
  scripts in a Taskfile.
---

# Repo optimization for AI agents

Transform a repository so agents (and humans) find what they need with
minimal context, reuse existing tooling instead of reinventing it, and get
identical feedback locally and in CI.

Three principles drive every step:

1. **Carry the common case; route the rest.** AGENTS.md is the working
   layer, not a router. It holds everything most tasks need, within a hard
   budget, so a typical task starts with zero extra reads. Content that
   only some tasks need lives in `docs/` behind an explicit, conditional
   route ("before you change CI, read docs/ci.md"), never a soft pointer.
2. **One home for scripts.** Every runnable thing is a Taskfile task, so
   agents discover commands with `task --list` instead of re-writing them.
3. **One definition of green.** Hooks, CI, and humans all run the same
   `task ci`.

The cost model behind the budget: AGENTS.md is prompt-cached, so its
tokens cost little per turn; a routing hop costs a whole tool turn on
every task that takes it; and instruction-following degrades as the number
of competing rules grows. The AGENTS.md budget is therefore **~150 lines /
~2000 estimated tokens (chars/4)** — roughly 40–60 distinct rules, about
where models start dropping some. Below it, inlining beats routing; above
it, each added rule makes the existing ones less likely to be followed, so
the overflow routes.

## Workflow

Work incrementally — each step leaves the repo better even if you stop there.

### 1. Audit and measure what exists

Inventory before touching anything: existing README/CLAUDE.md/AGENTS.md and
their sizes, loose scripts (`scripts/`, `bin/`, `package.json` scripts,
Makefile), doc sprawl, existing CI workflows and hooks, and how tool versions
are pinned. Record the **cold-start cost**: estimated tokens (chars/4) of
everything an agent loads before doing work (CLAUDE.md and its includes,
AGENTS.md, anything the README tells it to read first), and how many extra
reads a typical task (run the tests, fix a lint error, add a small feature)
needs before it can start. You will compare against both at the end. Fold
existing content into the new structure — never discard working scripts or
docs; relocate them.

### 2. Fill AGENTS.md first

Write AGENTS.md so that most tasks need nothing else. Add sections in this
priority order and stop when the budget is reached:

1. **Ground rules** every task obeys: reuse the Taskfile (`task --list`
   first), run the checks before committing, the never-do list.
2. **The command surface**: the tasks a typical change runs (setup, test,
   lint, check, ci), one line each, with the flags that matter.
3. **Where things live**: an annotated layout tree.
4. **Conventions most changes touch**: naming, testing, commits, branches.
5. **Gotchas**: what agents get wrong in this repo, and what never to do.
6. **Routes** to the docs that hold the rest (step 3 says how to word them).

Then make `CLAUDE.md` contain exactly `@AGENTS.md` — a pure include, so
there is one agent entrypoint and nothing to drift — and shrink `README.md`
to orientation, the quick start, and a link onward. If everything
agent-relevant fits in AGENTS.md (under ~2000 tokens in total), stop here:
no `docs/`, no `docs/index.md`. One file the agent already has beats a
Read call to reach the same content.

### 3. Route the overflow — and know when a route is needed

Content leaves AGENTS.md for a `docs/<topic>.md` when **any** of these
hold; otherwise it stays:

- it serves one kind of task only (deploys, migrations, a subsystem
  reference, a runbook, an API reference);
- it is long-form — procedures, tables, matrices, worked examples. The
  *rule* stays in AGENTS.md ("every new channel needs a registry entry");
  the *procedure and reference* go to the doc;
- it changes often, so it would keep invalidating the cached entry file;
- AGENTS.md would exceed its budget — cut the content that serves the
  fewest tasks first.

Content comes back into AGENTS.md when a routed doc turns out to be read
on nearly every task: a hop taken every time is a hop that should not
exist.

**Word every route as a conditional imperative**, in AGENTS.md and in the
index alike. The trigger comes first, then "read", then the file, then what
it holds:

- `Before you change CI, hooks or the check scripts, read docs/ci.md — it
  defines what `task ci` must keep running.`
- `When you add or edit a Taskfile task, read docs/tasks.md first.`

Never "see docs/ci.md for details", "more in docs/", or a bare link list:
agents treat soft pointers as optional and skip them, then reinvent what
the doc already settled. A stated trigger plus "read" gets followed. Close
the routes with a catch-all so uncovered tasks do not guess: `For any task
not covered above, read docs/index.md before you start.`

**Add `docs/index.md` only when it earns its hop**: when there are more
routed docs than fit as rows in AGENTS.md (more than ~6), or when tasks
arrive that AGENTS.md cannot anticipate. With fewer docs, route to them
directly from AGENTS.md — one hop. Either way, **at most two hops** from
AGENTS.md to the detail a task needs (AGENTS.md → docs/index.md → topic
doc); a doc that only routes onward again is a turn spent on nothing, so
merge it. Index rows use the same conditional-imperative wording.

Layout, per-file budgets, the content-depth test, and route wording
examples: read [references/docs-fanout.md](references/docs-fanout.md) when
the repo has more agent-relevant content than one AGENTS.md can hold.

### 4. Pin tooling with mise, centralise scripts in a Taskfile

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

### 5. Wire hooks and CI through the Taskfile

- Versioned hooks in `.githooks/` (activated via
  `git config core.hooksPath .githooks` inside a `task setup`):
  pre-commit → `task pre-commit`, pre-push → `task pre-push` → `task ci`.
- A GitHub Actions workflow that only checks out, installs tools with
  `jdx/mise-action` (reading `mise.toml`), and runs `task ci`. No check
  logic in YAML — if CI-only steps exist, contributors can't reproduce
  failures locally.

### 6. Add automated guardrail checks

Add stdlib-only scripts (invoked via `task check`) that keep the structure
from regressing:

- **Context-size budgets**: AGENTS.md ≤ ~150 lines / ~2000 tokens;
  docs/index.md ≤ ~100 lines / ~1000 tokens; topic docs ≤ ~300 lines;
  `CLAUDE.md == @AGENTS.md` verbatim. Have the check *print* the
  always-loaded total every run, not only fail on a budget — a cost that
  is visible gets managed.
- **Routing checks**: every route in AGENTS.md and docs/index.md is
  explicit (the line names a trigger and says "read"), and every topic doc
  has a route. An unrouted doc is invisible; a soft route is skipped.
- **Convention checks**: whatever the repo's docs promise (referenced files
  exist, every task has a `desc:`; for a skills repo, skill frontmatter and
  progressive-disclosure budgets).

Budgets are constants at the top of each script — changed deliberately, not
worked around. Concrete checks, budget values, and script skeletons: read
[references/checks.md](references/checks.md) only if the repo needs checks
beyond the ones above.

### 7. Verify and compare

Run `task ci` yourself before declaring done; where you cannot run
`task`, at least confirm `Taskfile.yml` parses as YAML (quoted `desc:`
lines, quoted `{{ }}` templates, block style) — a Taskfile that fails to
load is worse than the Makefile it replaced. Then measure the agent
experience against the step 1 baseline, starting from AGENTS.md alone:

- Is AGENTS.md within budget, and does it carry the command surface, the
  layout, and every rule that applies to most tasks?
- Does a typical task need **zero** extra reads, and a specialised one at
  most one (direct route) or two (via the index)?
- Is every route a conditional imperative with its trigger stated?

Report before and after in your summary: always-loaded tokens, and reads a
typical task needs before starting. If AGENTS.md is over budget, cut the
content serving the fewest tasks; if a common task still needs a hop, pull
that content in; if a route is soft, reword it.

## References

- [references/docs-fanout.md](references/docs-fanout.md) — what goes in
  AGENTS.md versus a routed doc versus the index, per-file budgets, route
  wording that gets followed.
- [references/tooling.md](references/tooling.md) — mise + Taskfile
  patterns, migrating existing scripts, sandbox bootstrap, hook wiring.
- [references/checks.md](references/checks.md) — guardrail check design,
  cold-start report, routing checks, reusable script skeletons.
