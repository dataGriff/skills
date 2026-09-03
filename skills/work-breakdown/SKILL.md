---
name: work-breakdown
description: >-
  Break a large piece of work into small, independently shippable units of
  delivery, each of which proves something and delivers value — customer
  value or a reduction in remaining work, risk, or uncertainty. Then deliver
  the units as small PRs, optionally in parallel using git worktrees, and
  optionally tracked as Linear sub-issues. Use when the user asks to break
  down, decompose, slice, or plan a piece of work, epic, feature, or
  migration; says a change or PR is (or will get) too big; wants to "deliver
  often", "ship incrementally", or avoid a big-bang release; asks to split
  work into sub-issues or milestones; or wants to parallelize work across
  branches or worktrees.
---

# Work breakdown into units of delivery

Turn one large piece of work into an ordered list of **units of delivery**:
small increments that each merge to the main branch, prove something, and
leave the world more valuable than before. Small units are worth the
slicing effort because each merge retires risk early, keeps every PR
reviewable, and means an interruption or a wrong assumption costs one unit,
not the whole piece of work.

## What counts as a unit of delivery

Every unit must pass all five tests. If a proposed unit fails one, reshape
it — don't waive the test.

1. **Shippable** — merges to main on its own and leaves the system
   releasable. Incomplete behaviour hides behind a feature flag or an
   unused code path rather than living on a long branch; an unmerged branch
   is inventory, not delivery.
2. **Proves something** — answers a real question: "the API can hold this
   shape", "the migration runs on production data", "users take the new
   path". If nothing is learned when it lands, fold it into a unit that
   does teach something.
3. **Valuable** — someone is better off once it merges. Customer value
   counts, but so does *reduction*: fewer things left to do, a risk
   retired, a dependency removed, a decision unblocked. "Sets up for later"
   alone is not value — say what got smaller or safer.
4. **Small** — a PR one reviewer holds in their head in one sitting
   (roughly a day or two of work; a few hundred lines of hand-written
   diff). Bigger than that, slice again.
5. **Independent enough** — states its dependencies on other units
   explicitly, and needs no unit that comes *after* it. Units with no
   dependency between them are candidates for parallel delivery.

## Workflow

### 1. Understand the work and name the end state

Restate the overall outcome in one or two sentences and get the user's
confirmation if it's ambiguous. List the major unknowns and risks —
technical ("does this scale?"), product ("will anyone use it?"), and
integration ("does system X actually behave as documented?"). The riskiest
unknowns shape the first units.

### 2. Slice vertically

Cut through the stack, not along it. A thin end-to-end slice (one
endpoint, one field, one happy path, wired from UI to storage) beats a
completed layer, because a layer proves nothing until everything above it
exists. Watch for the classic failure: units named after architecture
("build the schema", "build the service", "build the UI") — that's one big
unit in disguise, deferring all learning to the last merge.

Default first unit: a **walking skeleton** — the thinnest possible
end-to-end path through the real architecture, deployed for real. It
proves the plumbing and makes every later unit an extension instead of an
integration.

If the work resists slicing — a big refactor, a migration, a rewrite, or
every slice you try comes out horizontal — open
[references/slicing-patterns.md](references/slicing-patterns.md) for
named techniques (walking skeleton, branch by abstraction, strangler,
parallel change, SPIDR) and worked examples.

### 3. Order by risk, then by dependency

Sequence units so the riskiest assumptions are tested earliest — the most
valuable thing an early unit can deliver is the discovery that the plan is
wrong while it's still cheap. Then topologically order around explicit
dependencies. Flag the units with no path between them: those can run in
parallel.

### 4. Write the plan down

Produce the breakdown as a table the user can act on:

| # | Unit | Proves | Value delivered | Depends on |
|---|------|--------|-----------------|------------|
| 1 | Walking skeleton: `POST /orders` stores one hard-coded order | Deploy pipeline + service shape work end to end | Every later unit is an extension, not an integration | — |
| 2 | Real order validation behind flag | Domain rules fit the schema | Riskiest domain logic retired early | 1 |

Keep unit titles verb-first and concrete. If any row's "Proves" or "Value
delivered" cell is hard to fill, that unit fails the tests above — reshape
it before presenting the plan.

If the user tracks work in Linear (they mention Linear, or Linear MCP
tools are available), offer to create the breakdown as a parent issue with
one sub-issue per unit — open [references/linear.md](references/linear.md)
for the mapping and conventions before creating issues.

### 5. Deliver unit by unit

One unit = one branch = one PR = one merge. Finish and merge a unit before
judging the next one — a merged unit often changes what the next unit
should be, and re-planning between units is the point, not a failure.
After each merge, re-check the remaining plan: drop units the merge made
unnecessary, and re-slice any unit that has grown.

When two or more units have no dependency between them and the user wants
them in flight at once, isolate each in its own git worktree so parallel
units never share a dirty working tree — open
[references/worktrees.md](references/worktrees.md) for setup, naming, and
cleanup when doing this.

## References

- [references/slicing-patterns.md](references/slicing-patterns.md) —
  named slicing techniques with worked examples. Open when the work
  resists slicing or slices keep coming out horizontal.
- [references/linear.md](references/linear.md) — turning a breakdown into
  a Linear parent issue + sub-issues and driving delivery through them.
  Open when the user tracks work in Linear.
- [references/worktrees.md](references/worktrees.md) — git worktree
  mechanics for delivering independent units in parallel. Open when
  starting parallel delivery.
