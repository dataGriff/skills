# Fanout docs: layout and rules

## The shape

```
README.md ─┐
AGENTS.md ─┴─→ docs/index.md ─→ docs/<topic>.md ─→ (deeper refs as needed)
CLAUDE.md = "@AGENTS.md"
```

An agent's cold-start cost is README/AGENTS + index only; every deeper doc
is opt-in. Optimize for the reader who needs *one* topic, not the reader who
reads everything.

## When fanout pays

Each arrow above is a Read call — a tool turn on every task that follows
it — so routing is not free. Decide by size and shape:

| Agent-relevant docs        | Shape                                       |
| -------------------------- | ------------------------------------------- |
| under ~2000 tokens         | one AGENTS.md, no index; CLAUDE.md includes it |
| more, one kind of task     | AGENTS.md + one topic doc, linked directly  |
| more, several task types   | full fanout via docs/index.md               |

Two hops maximum from AGENTS.md to the detail a task needs. A page that
only routes onward again should be merged into its parent. If a routed
doc is needed by nearly every task, it belongs in AGENTS.md after all —
one file the agent already has beats a Read call on every task.

## Budgets (starting points — enforce them with a check script)

| File            | Lines | ~Tokens | Purpose                              |
| --------------- | ----- | ------- | ------------------------------------ |
| README.md       | ≤60   | ≤600    | human orientation + quick start      |
| AGENTS.md       | ≤60   | ≤800    | agent ground rules + routing table   |
| docs/index.md   | ≤100  | ≤1200   | routing table + repo layout          |
| docs/<topic>.md | ≤300  | —       | one concern, fully covered           |

## What goes in each file

**README.md** — what the repo is, the 3-command quick start, a prominent
link to docs/index.md. No conventions, no architecture.

**AGENTS.md** — only rules that apply to *every* task: reuse the Taskfile
(`task --list` first), run the checks, where things live, plus a small
routing table for common task types. Everything else routes.

**CLAUDE.md** — exactly `@AGENTS.md`. Claude Code expands the include, so
agent guidance has a single source. Any real content here will drift from
AGENTS.md.

**docs/index.md** — a table with one row per doc: doc name + "read it when
you are …". Also a short annotated repo layout tree. Nothing else.

**Topic docs** — the actual detail. One concern per file (setup, CI,
contributing, architecture, domain conventions). If one grows past budget,
split it and add routes.

## Content-depth decision

For any piece of content, ask "who needs this and when?":

- Every task, always → AGENTS.md (be very reluctant; this taxes everything).
- A category of tasks → a topic doc, routed from index.
- One component/skill/module → a reference file inside that component.
- Nobody, currently → delete it; stale docs cost trust as well as tokens.

## Anti-patterns

- A "quick reference" section in AGENTS.md that mirrors docs — duplication
  is how routers regress into monoliths. Link instead.
- Docs without a route from index — invisible to agents, guaranteed to rot.
- Raising a budget to make a check pass — the budget *is* the feature.
