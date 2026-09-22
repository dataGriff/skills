---
name: repo-declutter
description: >-
  Strip noise from a repository so humans and agents read less for the same
  knowledge: cut verbose or duplicated doc prose, move history and narrative
  out of docs into git (changelog sections, "previously we…", migration
  diaries), delete comments that restate code, commented-out code, stale
  TODOs and banner comments, and replace comments that paper over unclear
  code with a behaviour-preserving rename or extract. Audits first (a
  findings table: what, where, why, action, what git already holds), then
  applies one reviewable commit per category with tests green; never removes
  licences, security notes, agent rules, API contracts or comments that
  explain a constraint. Use when asked to declutter, tidy, cleanse, slim or
  de-noise a repo, README, docs or comments, to remove stale or redundant
  comments or commented-out code, to make docs succinct or less verbose, or
  to move history out of docs into git.
---

# Repo declutter

Noise is text that costs reading and buys no decision. This skill removes
it from docs, comments and, through renames, from code — so that a reader,
human or agent, learns the same things from fewer words. The risk that
matters is the opposite failure: deleting signal. So the protected list
comes before the workflow, and the audit comes before any edit.

## Principles

0. **Signal stays.** Never remove: licence and copyright headers, SPDX
   lines; security notes ("never log", "never commit .env"); rules agents
   or contributors must follow; API contracts, invariants and compatibility
   promises; decisions still in force (ADRs, "we use X because Y" where Y
   still holds); comments that explain a non-obvious constraint, workaround,
   why-not, or point at a ticket, RFC or spec. When you cannot tell whether
   a decision is still in force, keep it and mark the row "verify" in the
   audit — a reviewer can delete in seconds what a reader cannot recover.
1. **Docs state the present; git holds the past.** What used to be true,
   when it changed, and how a migration went belong in a commit message,
   `CHANGELOG.md`, or a release note. A doc says how things are.
2. **Code explains what; comments explain why.** A comment that restates
   the next line is deleted. A comment that compensates for a bad name is
   replaced by a good name, then deleted.
3. **Behaviour never changes.** Rename and extract-function only; tests
   green before and after; one commit per category so a reviewer can accept
   or revert each on its own.

## Workflow

1. **Baseline.** Run the test suite and record the result; a suite that
   already fails means no code changes this pass — docs and comments only.
   Note each doc's size (chars/4 ≈ tokens). For a handful of files, read
   them. When the repo has more than ~15 doc or source files, or a full
   audit was asked for, run `python3 scripts/audit_noise.py <repo>` for
   the per-file numbers instead of hand-scanning.
2. **Audit.** Write `DECLUTTER-AUDIT.md` at the repo root, one row per
   finding:

   `| # | file:line | category | what | why noise | action | git holds |`

   Categories: `prose`, `history`, `duplicate`, `comment`, `code-clarity`.
   For `history` rows, `git holds` says whether git already tells the
   story (`git log -S"<phrase>" --oneline`, `git log --follow <file>`) —
   then delete — or not — then the removal commit body carries the gist.
   End with a **Protected — kept** list so the reviewer sees what was left
   on purpose. Stop here when only an audit was asked for.
3. **Apply**, safest first, one commit per category: docs (`prose`,
   `duplicate`) → `history` → `comment` → `code-clarity`. Subject
   `declutter(<category>): <one line>`; the body carries the gist of any
   removed narrative — that body is where history now lives. Update each
   row's action to `done: <commit>`.
4. **Verify.** Tests green; `git diff --stat` per commit; re-measure; report
   before and after in your summary (doc tokens, comment lines, findings
   closed and deferred).

## What counts as noise

| Category       | Signals                                                                                                        | Action                                                                                  | Watch for                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `prose`        | hedges ("it is worth noting", "basically", "in order to", "please note", "simply", "just"); sentences over ~30 words; a paragraph that says one thing twice | rewrite: lead with the rule, one idea per sentence, a table for parallel facts; keep every fact, command and path | a "why" sentence that is a decision still in force            |
| `history`      | "previously", "used to", "as of vN", "we switched/migrated/renamed", dated entries, a History/Changelog/What's-new heading inside a doc that is not a changelog | move the gist to the removal commit body or `CHANGELOG.md`; leave one line of current state if the doc needs it | a migration guide readers still follow; an ADR                |
| `duplicate`    | the same install steps, command or rule in two docs                                                            | keep the home the entry file routes to; replace the other copy with a route line        | a one-line rule repeated in AGENTS.md on purpose              |
| `comment`      | restates the next line; commented-out code; TODO/FIXME with no owner or ticket, or older than what it waits for; banner rules; "added by / modified on"; autogenerated stubs | delete                                                                                  | a TODO with a live ticket; a "why" comment beside odd-looking code |
| `code-clarity` | a comment naming what a parameter or variable means; a "does X then Y" header over a long function             | rename the identifiers, or extract the Y block into a named function; delete the comment only once the name carries it | public exports (out of scope; note in the audit)              |

## Safety rules for code

- Only rename and extract. No reordering, no condition changes, no
  signature changes beyond parameter renames — and update every keyword
  call site.
- Grep every call site before a rename, including tests, docs and config.
- Run the suite after each file, not at the end.
- A rename that touches a public export changes the API: leave it, record
  it in the audit as a proposal.
- A bug you notice is a separate finding, never a fix in this pass.

## History belongs in git

The removal commit body is the narrative's new home: what was removed and
the one-paragraph gist ("HTTP layer moved from Flask to FastAPI in v2; v1
API dropped"). A doc section that really is a changelog moves to
`CHANGELOG.md`, or becomes a pointer to releases when the repo has them.
Every moved item appears in the audit with its commit hash, so nothing
leaves silently.

## When not to declutter

- The test suite fails: code stays untouched (docs and comments may still
  go).
- Generated, vendored, or externally licensed files.
- `CHANGELOG.md`, ADRs, post-mortems, migration guides: history is their
  purpose.
- Comments in a public SDK, a config template, or an example users copy.
- A repo mid-migration, where the "previously" sentences are the guide.
- Asked about docs only: leave code alone, and the reverse.
- The problem is *where* content lives rather than *how much* exists: that
  is the `repo-optimization` skill; run this one on a doc it keeps.

## References

- [references/detection.md](references/detection.md) — regex-level signals
  per category, false positives, before/after examples; open when a finding
  does not fit the table above or the script's report needs interpreting.
- [references/comments.md](references/comments.md) — what a good comment
  is and the rename/extract recipe; open when applying `comment` or
  `code-clarity` findings.
- [references/prose.md](references/prose.md) — rewrite rules and a worked
  example; open when a doc section is rewritten rather than deleted.
- [scripts/audit_noise.py](scripts/audit_noise.py) — stdlib scan that
  prints per-file noise tables; run when the repo is too large to
  hand-scan (step 1 states the threshold).
