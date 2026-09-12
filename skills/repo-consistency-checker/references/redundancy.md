# Redundancy: what counts, where the fact should live, how to find dead code

## Why redundancy is a consistency problem

Two copies of a fact cannot stay equal without a mechanism that keeps
them equal, and prose has no such mechanism. Every duplicated statement is
a future drift finding; every dead function is a claim ("this is used")
that is already false. Removing redundancy is therefore not tidiness — it
is removing the places where the next inconsistency will appear.

## Taxonomy

| Kind | Looks like | Why it matters |
|---|---|---|
| Duplicated fact | the same rule, limit, command or explanation in README and CONTRIBUTING; in a doc and a comment; in a doc and a constant | the copies diverge; readers trust whichever they find first |
| Dead code | unused functions, exports, classes, branches, parameters, feature flags stuck on/off | describes behaviour that does not happen; costs reading time and maintenance |
| Duplicated code | copy-pasted helpers, two implementations of the same parsing or formatting | fixes land in one copy |
| Commented-out code | blocks of code behind comment markers | git already keeps history; the block raises "is this still needed?" for every reader |
| Stale markers | TODO / FIXME for work that has landed or been dropped | a to-do list nobody reads is a false claim about pending work |
| Orphan docs | docs nothing links to, docs for removed features, old runbooks | found by search, believed, wrong |
| Superseded config | keys nothing reads, scripts nothing calls, CI jobs for nothing, dependencies nothing imports | implies behaviour that does not exist; slows every audit |
| Redundant comments | a comment that restates the line below in English | doubles the text a reader must reconcile and drifts when the line changes |

## What is not redundancy

- **Routing pointers.** "Testing: see docs/testing.md" is a link, not a
  copy. Fanout layouts (small entry file, topic docs) rely on them.
- **A deliberate one-line summary** that links to its source. Two
  sentences of orientation before a link is fine; a paragraph that stands
  on its own is a copy.
- **Historical records.** CHANGELOG entries, ADRs, migration guides and
  release notes describe a moment. They are only a problem when linked
  as current guidance or when a current doc contradicts them without
  saying the decision was superseded.
- **Generated or vendored files.** Not authored here; audit their source.
- **Test isolation.** Repeated setup in tests is often intentional so
  each test reads alone; flag only when the repetition hides a helper that
  already exists.
- **Documentation for different audiences.** A user guide and an API
  reference may cover the same feature. The test is whether they state the
  same *fact* (a limit, a default) in two places — that fact should be
  stated once and referenced.

## Choosing the canonical home

When a fact appears in several places, keep the copy that is:

1. **Enforced** — a constant with a check behind it, a task definition, a
   schema, a test. Code that runs cannot go stale without failing.
2. Failing that, **closest to the code** — the docstring over the
   function, the comment beside the constant, the `desc:` of the task.
3. Failing that, **the most-read doc** on the path an agent or human
   actually takes (README, AGENTS.md, docs index).

Every other copy becomes a pointer ("budget: see `MAX_LINES` in
`scripts/check.py`") or is deleted. If the fact must be stated in prose
for readers who will never open the code, state it *once* and make the
doc the place the comment points to — never both ways.

Before deleting a copy, confirm the surviving copy is reachable from where
the deleted one was found: a reader who lands on the old location must
still be able to get to the fact in one hop.

## Finding dead code

Start with a repo-wide search for the exact name — in code, strings,
templates, config, CI and docs — because dynamic dispatch, reflection,
plugin registries and string-based lookups hide callers from static
tools. Then, for anything larger than a few files, use the language's
tooling:

| Language | Tool | Notes |
|---|---|---|
| Python | `vulture .`, `ruff --select F401,F841`, `pyflakes` | vulture reports confidence; anything under 80 % needs a manual search |
| JS / TS | `knip`, `ts-prune`, `eslint no-unused-vars`, `depcheck` for dependencies | knip covers unused files, exports and deps in one run |
| Go | `staticcheck -checks U1000`, `deadcode ./...` | exported identifiers in a library are public API, not dead |
| Rust | `cargo build` warnings (`dead_code`), `cargo udeps` for deps | |
| Java / Kotlin | IDE inspections, `ArchUnit` for layering claims | |
| C# | `dotnet build` warnings, Roslyn analyzers | |
| Shell / Make / Taskfile | search each target name across hooks, CI, docs and other targets | a target only ever called by hand is not dead; ask |
| Config keys | search each top-level key from the config file in the code | keys read through a generic loader (`config[name]`) need the loader's call sites |

Public API is the exception: an exported function with no in-repo caller
may be used by consumers you cannot see. Flag it as "no in-repo callers"
and let the owner decide.

## Finding duplicated code

Search for distinctive lines (an error message, a regex, a magic number)
and for function names that differ only by prefix or suffix (`format_x`,
`format_x_v2`, `legacy_format`). Language duplicate detectors (`jscpd`
for most languages, `pylint --disable=all --enable=duplicate-code` for
Python) find the copy-pasted blocks that renaming hides.

## Removing safely

- Remove a dead function together with its tests, imports, docs, config
  and any comment that names it — otherwise the removal creates new drift.
- Delete commented-out code outright; mention the commit in the message
  if anyone might want it back.
- When deleting a duplicated doc section, redirect: leave the heading with
  a one-line pointer if inbound links or readers' habits point there.
- Run the repo's own checks after each group of removals; an unused
  import removed from the wrong module is a syntax error at best.
