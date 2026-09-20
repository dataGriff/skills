# Docs style: AGENTS.md first, then the fanout

Documentation in this repo is shaped for agents whose context is a finite
budget and whose attention is a finite number of rules. The rule: **carry
the common case in AGENTS.md; route the rest, explicitly.**

## How it works

```
README.md  ──→ orientation + quick start
AGENTS.md  ──→ what most tasks need, within budget (CLAUDE.md = @AGENTS.md)
   ├──→ docs/<topic>.md                (direct routes for common task types)
   └──→ docs/README.md ──→ docs/<topic>.md   (catch-all for everything else)
```

- `AGENTS.md` is the working layer, not a router: ground rules, commands,
  layout, the conventions most changes touch, and the routes. A typical
  task needs nothing else.
- `CLAUDE.md` contains exactly `@AGENTS.md` — one agent entrypoint, no
  duplication to drift.
- `docs/README.md` is the fallback: one row per doc saying when to read it,
  for tasks AGENTS.md does not anticipate. It is a README rather than an
  index.md so the repo UI renders it in place when you browse `docs/`; the
  same goes for any directory that needs a map — but each README is a
  routing hop, so add one only where a directory holds enough to need it.
- Topic docs hold the detail, each focused on one concern.

## Why the AGENTS.md budget is what it is

AGENTS.md is prompt-cached, so its tokens are cheap per turn, while every
routing hop costs a whole tool turn on every task that takes it — so
inlining wins until the file itself becomes the problem. It becomes the
problem through rule count: instruction-following degrades as competing
rules accumulate, and ~150 lines holds roughly 40–60 rules, about where
models begin to drop some. Hence ≤150 lines / ~2000 tokens, enforced by
`task check:context`. Lower it if agents visibly ignore rules; never raise
it.

## Rules for writing docs

1. **Put content at the right depth.** Needed by most tasks → AGENTS.md
   (the rule itself; the reasoning and examples can live in a topic doc).
   Needed by one kind of task → a `docs/` topic file. Needed only inside
   one skill → that skill's `references/`. Needed by nobody → delete it.
2. **Every doc gets an explicit route.** In AGENTS.md (common task types)
   or `docs/README.md` (everything else), as a row whose first cell is the
   trigger and whose second cell starts with "Read". "See docs/x.md" is
   decoration agents skip; `task check:context` fails on it, and on any
   topic doc with no route at all.
3. **Move content in as well as out.** A topic doc that nearly every task
   reads belongs in AGENTS.md; a section of AGENTS.md that only one kind
   of task uses belongs in a topic doc. Cut what serves the fewest tasks
   first when the budget trips.
4. **Stay in budget.** `task check:context` enforces line/token budgets on
   README, AGENTS.md, docs/README.md, topic docs, and SKILL.md files. When a
   check fails, move content deeper — don't raise the budget.
5. **Don't repeat detail, link it.** Repeating a one-line rule in AGENTS.md
   is fine; repeating a procedure is how routers bloat back into monoliths.
