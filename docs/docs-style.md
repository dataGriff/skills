# Docs style: the fanout

Documentation in this repo is shaped for agents whose context is a finite
budget. The rule: **route early, load late.**

## How it works

```
README.md ─┐
AGENTS.md ─┴─→ docs/index.md ─→ docs/<topic>.md ─→ (skill references, etc.)
```

- `README.md` and `AGENTS.md` are tiny. They orient and immediately route to
  `docs/index.md`.
- `CLAUDE.md` contains exactly `@AGENTS.md` — one agent entrypoint, no
  duplication to drift.
- `docs/index.md` is a routing table: one line per doc saying when to read it.
- Topic docs hold the actual detail, each focused on one concern.

An agent starting a task loads at most README/AGENTS + index (~a few hundred
tokens) and then only the one topic doc it needs. Detail is never wasted on
tasks that don't need it.

## Rules for writing docs

1. **Put content at the right depth.** Universally needed → AGENTS.md
   (sparingly). Needed for a category of task → a `docs/` topic file, routed
   from index. Needed only inside one skill → that skill's `references/`.
2. **Every new doc gets a route.** Add a row to the table in
   `docs/index.md` saying when to read it. An unrouted doc is invisible.
3. **Stay in budget.** `task check:context` enforces line/token budgets on
   README, AGENTS.md, docs/index.md, topic docs, and SKILL.md files. When a
   check fails, split the file and push detail deeper — don't raise the
   budget.
4. **Don't repeat, link.** Repetition across levels is how routing files
   bloat back into monoliths.
