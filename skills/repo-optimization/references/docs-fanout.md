# AGENTS.md first, then the fanout: layout and rules

## The shape

```
README.md  ──→ orientation + quick start, then points at AGENTS.md / docs
AGENTS.md  ──→ the working layer: what most tasks need, within budget
   │  explicit conditional routes ("before you X, read docs/Y.md")
   ├──→ docs/<topic>.md              (few routed docs: link them directly)
   └──→ docs/index.md ──→ docs/<topic>.md   (many routed docs: one index hop)
CLAUDE.md = "@AGENTS.md"
```

An agent's always-loaded cost is AGENTS.md alone. The index and every
topic doc are opt-in, taken only when a task's trigger fires. Optimise for
the reader doing a typical task, who should need nothing beyond AGENTS.md,
and then for the reader doing one specialised task, who should need one
more file.

## Budgets (starting points — enforce them with a check script)

| File            | Lines | ~Tokens | Purpose                                         |
| --------------- | ----- | ------- | ----------------------------------------------- |
| README.md       | ≤60   | ≤600    | human orientation + quick start                 |
| AGENTS.md       | ≤150  | ≤2000   | ground rules, commands, layout, conventions, routes |
| docs/index.md   | ≤100  | ≤1000   | routing table for tasks AGENTS.md does not cover |
| docs/<topic>.md | ≤300  | —       | one concern, fully covered                      |

Why 150 lines / 2000 tokens for AGENTS.md: the file is prompt-cached, so
its tokens are cheap per turn, while every route costs a whole tool turn
on every task that takes it — so inlining wins until the file itself
becomes the problem. It becomes the problem through rule count, not size:
instruction-following degrades as competing rules accumulate, and ~150
lines holds roughly 40–60 rules, about where models begin to drop some.
Past that, adding a rule makes the existing ones less reliable. The number
is a starting point; a repo whose agents visibly ignore rules should lower
it, never raise it.

## What goes in each file

**README.md** — what the repo is, the 3-command quick start, a link to
AGENTS.md or docs/. No conventions, no architecture.

**AGENTS.md** — in priority order, stopping at the budget:

1. Ground rules every task obeys: reuse the Taskfile, run the checks, the
   never-do list.
2. The command surface: the tasks a typical change runs, one line each.
3. Where things live: an annotated layout tree.
4. Conventions most changes touch: naming, tests, commits, branches.
5. Gotchas: what agents get wrong here.
6. Routes to the docs holding the rest, plus a catch-all route to the
   index (or, with no index, "ask before inventing a convention").

**CLAUDE.md** — exactly `@AGENTS.md`. Claude Code expands the include, so
agent guidance has a single source. Any real content here drifts.

**docs/index.md** — a table with one row per doc: the trigger, then "read
<doc>", then what it holds. Nothing else: no layout tree (that is in
AGENTS.md), no prose that re-explains the repo.

**Topic docs** — the actual detail. One concern per file (setup, CI,
deploys, a subsystem reference, a runbook). If one grows past budget,
split it and add routes.

## The content-depth test

For any piece of content, ask "who needs this and when?":

- Most tasks → AGENTS.md. This includes universal rules ("money is always
  `Decimal`", "never log message bodies") even when a topic doc also
  explains them: the rule lives in AGENTS.md, the reasoning, procedure and
  examples live in the doc. Duplicating the one-line rule is fine;
  duplicating the detail is how routers regress into monoliths.
- One kind of task → a `docs/<topic>.md`, routed with a trigger.
- One component/skill/module → a reference file inside that component.
- Nobody, currently → delete it; stale docs cost trust as well as tokens.

Content moves *out* of AGENTS.md when it serves one kind of task, is
long-form (procedures, tables, matrices, examples), changes often, or
would push AGENTS.md past budget — cut what serves the fewest tasks first.
Content moves *back in* when its doc turns out to be read on nearly every
task.

## When the index is needed

| Routed docs                    | Shape                                                |
| ------------------------------ | ---------------------------------------------------- |
| none (all fits in AGENTS.md)   | one AGENTS.md; no `docs/`, no index                  |
| up to ~6                       | AGENTS.md routes to each doc directly — one hop      |
| more than ~6, or tasks AGENTS.md cannot anticipate | AGENTS.md routes its common cases directly and the catch-all to docs/index.md — two hops maximum |

Two hops is the ceiling: AGENTS.md → docs/index.md → topic doc. A page
that only routes onward again is a turn spent on nothing; merge it into
its parent.

## Route wording that gets followed

A route is an instruction, not a hyperlink. Agents treat "see also" and
bare link lists as optional, skip them, and then reinvent what the doc
already settled. Every route — in AGENTS.md and in index rows — states its
trigger and says "read":

| Soft (skipped)                          | Explicit (followed)                                                   |
| --------------------------------------- | --------------------------------------------------------------------- |
| See docs/ci.md for CI details.          | Before you change CI, hooks or the check scripts, read docs/ci.md.    |
| More on tasks: docs/tasks.md            | When you add or change a Taskfile task, read docs/tasks.md first.     |
| Docs live in docs/.                     | For any task not covered above, read docs/index.md before you start.  |
| docs/deploy.md — deployment             | Read docs/deploy.md before you touch anything under `deploy/`.        |

Template: **trigger → "read" → file → what it holds**. In a table, the
trigger is the first cell and the second cell starts with "Read". A check
script can hold this line: every line in AGENTS.md or docs/index.md that
links a doc must contain "read" (or open/load/follow) and a trigger word
(before/when/if/whenever/unless/first/any task).

## Anti-patterns

- A "quick reference" in AGENTS.md that copies whole sections of a topic
  doc — carry the rule, route the detail.
- An index for two docs — that is a hop with no fanout; link them from
  AGENTS.md directly.
- A routed doc that nearly every task reads — it belongs in AGENTS.md.
- Docs without a route — invisible to agents, guaranteed to rot.
- Routes without a trigger — "see docs/" is decoration, not routing.
- Raising a budget to make a check pass — the budget *is* the feature.
