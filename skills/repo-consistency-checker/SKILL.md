---
name: repo-consistency-checker
description: >-
  Audit a repository for internal consistency: check that every fact stated
  in docs, comments, docstrings, config and help text matches the code that
  actually exists (commands, paths, names, versions, numbers, behaviour), and
  strip redundancy — the same fact stated twice, dead or duplicated code,
  orphan or stale docs, done TODOs, commented-out code — so each fact has one
  source of truth. Produces an evidence-backed findings table and applies the
  fixes on request. Use when the user asks to check a repo, PR or change for
  consistency or drift, for stale or outdated docs/comments, for docs that
  do not match the code, for duplicated or redundant content, for dead code,
  or for a single-source-of-truth cleanup; after a refactor, rename or
  removal; before a release; or when they say "tidy up", "audit", "are the
  docs still right", "is anything out of date", or "does the code do what
  the comments say".
---

# Repo consistency check

A repository is consistent when every statement it makes about itself is
true and made once. Statements live in docs, comments, docstrings, help
text, config comments and examples; the truth lives in whatever actually
runs — code, config, task runners, CI, tests. The two drift apart whenever
code changes and its descriptions don't, and they drift fastest where the
same fact is written in several places, because the second copy is the one
nobody updates.

Three rules shape the audit:

1. **Every claim gets checked against something that runs.** A doc sentence
   is a hypothesis; the Makefile target, the constant, the function
   signature or the test is the evidence. Never mark a claim consistent
   because it *sounds* plausible — find the referent.
2. **Every fact lives once.** Where a fact is stated twice, one copy is
   already wrong or soon will be. The canonical home is the copy closest to
   enforcement (the constant, the task definition, the test); every other
   place links to it or is deleted. A pointer ("see docs/ci.md") is not a
   duplicate; a restatement is.
3. **A finding is two locations and a quote from each.** "Docs are out of
   date" is not actionable. "`README.md:42` says X, `Makefile:17` defines
   Y" is.

Decide direction per finding, not globally. Usually the code is right and
the description stale; sometimes the doc records the intended behaviour and
the code regressed. Flag the second case as a possible bug instead of
silently rewriting the doc to bless the regression.

## Workflow

### 1. Scope and inventory

Fix the scope: the whole repo, one package, or the files a change touches
(a PR audit). Then list the two sides:

- **Claim sources** — README and docs/, AGENTS.md / CLAUDE.md /
  CONTRIBUTING, comments and docstrings, CLI help and task `desc:` lines,
  config comments and example files, error messages, code snippets in
  docs, CI workflow and job names, PR and issue templates.
- **Truth sources** — the code, the task runner (Taskfile / Makefile /
  package.json scripts), config and lockfiles, CI workflow steps, hooks,
  tests.

Use git to aim. `git log --diff-filter=RD --name-status -50` lists recent
renames and deletions, and `git log --stat -20 -- <dir>` shows what changed
lately without the docs that describe it. Drift concentrates around recent
renames, deletions and refactors, so check their descriptions first.

### 2. Run the mechanical scan

`scripts/scan_consistency.py` (stdlib-only; run it from the repo root as
`python3 <skill-dir>/scripts/scan_consistency.py [path] [--json]`) finds
the classes of drift that are cheap to detect and expensive to miss:

- relative paths and markdown links, in docs and in code comments, that
  point at files that no longer exist;
- `task X` / `make X` / `npm run X` / `pnpm X` mentions whose target is
  not defined anywhere in the repo;
- paragraphs repeated near-verbatim across files (duplicate facts);
- docs nothing links to (orphans) — the usual trace of a removed feature;
- commented-out code blocks and TODO / FIXME markers to re-check;
- numeric claims in prose ("at most 500 lines", "retries 3 times"), each
  with the code lines that carry the same number, for manual comparison.

Run it on any repo larger than a handful of files, then treat its output
as leads, not findings: every hit still needs the two-location evidence of
step 3, and the scan cannot see semantic drift at all.

### 3. Verify claims against their referents

Work through the claim sources in reading order and, for each checkable
claim, find the thing it describes and compare. The claim types that drift
most, and what settles each:

| Claim type | Example | Settled by |
|---|---|---|
| Command | "run `make test`" | the target exists and does what the sentence says |
| Path / filename | "config lives in `settings.yaml`" | the file exists at that path |
| Identifier | flag, env var, config key, function named in prose | a search finds a definition with that exact name |
| Number / limit | "under 500 lines", "3 retries", "port 8080" | the constant or config value that enforces it |
| Version | "requires Python 3.12" | the pin in the manifest, mise file, or CI |
| Behaviour | "returns None when missing" | the code path, and its test |
| Sequence | numbered setup steps | each step still exists and the order still works |
| Structure | "X calls Y", a layout tree in the README | imports; a directory listing |
| Signature | docstring params, a comment above a function | the actual parameters and return |
| Example | a code block in docs | it parses, and names only things that exist |
| Parity | "hooks run the same checks as CI" | hook script and CI workflow call the same entrypoint |

Comments get the same treatment as docs: read the comment, then the code
under it, and ask whether a reader trusting the comment would be misled. A
comment that restates the code line by line is redundancy (rule 2); one
that contradicts the code is drift (rule 1).

Verification recipes per claim type, including what to search for and the
false-positive traps, are in
[references/claim-types.md](references/claim-types.md) — open it when a
claim type is not obvious to check, such as behaviour claims, doc examples,
or generated files.

### 4. Hunt redundancy

Redundancy is anything the repo could lose without losing information or
behaviour. Look for:

- **Duplicated facts** — the same rule, number, command or explanation in
  two docs, in a doc and a comment, or in a doc and a constant. The scan
  finds verbatim copies; paraphrases need reading. Pick the canonical home
  by proximity to enforcement, keep that copy, and replace the others with
  a link or delete them.
- **Dead code** — functions, exports, branches, feature flags, config keys
  and dependencies nothing references. Confirm with a repo-wide search for
  the name (including strings, templates and config) before calling
  anything dead; dynamic dispatch and reflection hide callers.
- **Duplicated code** — copy-pasted helpers that should be one.
- **Stale residue** — commented-out code (git remembers it), TODOs about
  work that has landed, docs for removed features, "recently changed"
  notes that are years old, example files for defunct paths.
- **Superseded config** — keys nothing reads, scripts nothing calls,
  workflows for jobs that no longer exist.

Not redundancy: routing pointers, a one-line summary that links to the full
source, historical records (CHANGELOG, ADRs, migration notes — they
describe the past, not the present, and are only wrong if presented as
current guidance), vendored or generated files, and test setup repeated
for isolation. Leave those alone and say so in the coverage note.

The canonical-home rule in detail and dead-code tooling per language are
in [references/redundancy.md](references/redundancy.md) — open it when the
repo is too large for search alone, or when the right home for a
duplicated fact is unclear.

### 5. Report

Present findings as a table the user can act on line by line, most
damaging first:

| # | Kind | Severity | Claim | Truth | Fix |
|---|------|----------|-------|-------|-----|
| 1 | drift | misleading | `README.md:18` "run `make test`" | `Makefile:12` defines `test-unit`; no `test` target | README → `make test-unit` |
| 2 | drift | misleading | `app.py:40` docstring "returns None when missing" | `app.py:47` raises `WidgetNotFound` | rewrite docstring; or possible bug if callers expect None — check callers |
| 3 | redundant | low | `CONTRIBUTING.md:5-19` repeats the README setup section, pinned to 3.11 | `README.md:9-23`; `pyproject.toml` pins 3.12 | delete the copy, link to README |
| 4 | dead | low | `helpers.py:30` `legacy_format` | no references outside its definition | delete |

Kind: **drift** (claim ≠ truth), **redundant** (fact stated more than
once), **dead** (nothing uses it), **possible bug** (the claim is right and
the code is wrong). Severity: **misleading** — a reader acting on it does
the wrong thing (wrong command, path, value, behaviour); **stale** —
outdated but harmless; **low** — redundancy or noise.

Close the report with a **coverage** note: what was checked (which claim
sources, whether the scan and the tests ran), what was deliberately not
flagged and why, and what could not be verified. An audit that reports
only findings hides its own blind spots.

### 6. Fix, when asked or in scope

Fix in severity order, one logical group per commit (commands, then paths,
then numbers…) so a reviewer can verify each group by the same method you
used to find it. For each fix:

- **Drift**: change the claim to match the truth — unless the claim is the
  intended behaviour, in which case leave the code alone and raise the
  possible bug.
- **Redundancy**: delete the non-canonical copy and, where a reader would
  land there, leave a one-line pointer. Confirm the fact survives somewhere
  the repo's docs route to before deleting it.
- **Dead code**: remove it with its tests, imports, config and docs.

Re-run the scan and the repo's own checks (its `check` task, the test
suite, the linter) at the end. A cleanup that breaks the build is the one
inconsistency nobody forgives.

## References

- [references/claim-types.md](references/claim-types.md) — per-type
  verification recipes and false-positive traps. Open when a claim is not
  obvious to verify.
- [references/redundancy.md](references/redundancy.md) — redundancy
  taxonomy, choosing the canonical home, dead-code tooling per language.
  Open when hunting redundancy in a large repo or deciding where a
  duplicated fact should live.
- `scripts/scan_consistency.py` — mechanical scan for broken references,
  undefined commands, duplicate paragraphs, orphan docs, commented-out
  code, markers and numeric claims. Run it; open it only if it errors.
