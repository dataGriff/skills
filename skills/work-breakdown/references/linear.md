# Tracking a breakdown in Linear

How to turn a work breakdown into Linear issues and drive delivery through
them. Use whatever Linear access the session has (Linear MCP tools, or the
`linear` CLI if the user has one); if none is available, produce the
structure below as text the user can paste, and say that connecting the
Linear MCP server would let you create and update the issues directly.

## Structure: one parent, one sub-issue per unit

- **Parent issue** = the piece of work. Title is the outcome ("Billing
  supports multiple currencies"), not an activity. Description holds the
  end-state statement, the named risks, and the breakdown table from the
  plan — the parent is where the whole shape lives.
- **Sub-issue** = one unit of delivery, created via the parent's
  sub-issue relation (not merely a linked issue — sub-issues give Linear
  its progress rollup on the parent).
- Do **not** create sub-issues for horizontal tasks inside a unit
  ("write tests", "update docs") — those are part of the unit's
  definition of done, and separate issues for them invite delivering
  layers instead of slices.

## Sub-issue content

Title: verb-first and concrete, same as the unit title ("Accept currency
code end-to-end, hard-wired to USD").

Description — carry the two cells that justify the unit's existence, plus
its edges:

```
**Proves:** the schema/API/UI all carry a currency without breakage.
**Value:** every later currency unit is an extension, not an integration.
**Depends on:** — (none / ABC-121)
**Out of scope:** conversion, backfill, any currency other than USD.
```

The **Out of scope** line is what keeps units small in practice: scope
creep during delivery gets cut and pasted into a later sub-issue instead
of growing the PR.

Ordering and dependencies: order sub-issues in the parent to match the
delivery order, and use Linear's *blocks / blocked by* relations for real
dependencies. Sub-issues with no blocking relation between them are the
parallel candidates. Set estimate/priority/cycle only if the user's team
uses them — ask rather than invent values.

## Driving delivery

- One sub-issue = one branch = one PR. Use Linear's branch-name format if
  the workspace has one (copyable from the issue; typically
  `username/abc-123-slug`) and put the issue ID in the PR title or body —
  with GitHub integration enabled, `Fixes ABC-123` (magic words: `fixes`,
  `closes`, `resolves`, etc.) links the PR and auto-moves the issue to
  Done on merge.
- Move the sub-issue to In Progress when its worktree/branch starts, and
  let the PR merge close it. The parent's progress bar then reflects
  real merged delivery, not claimed progress.
- **Re-plan in the tracker, not just in your head.** After each merge,
  revisit the remaining sub-issues: cancel ones the merge made
  unnecessary (state why in a comment — a cancelled sub-issue is
  delivered reduction), split any that grew, and add newly discovered
  units as new sub-issues. A breakdown that never changes after contact
  with reality is a warning sign, not a virtue.
- Close the parent only when the end state is true, which may be before
  every original sub-issue is done — remaining nice-to-haves become
  ordinary backlog issues, not a reason to keep the parent open.
