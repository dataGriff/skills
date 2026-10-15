# Handover: capturing what one person knows

Use when a maintainer is leaving, changing teams, or is the only holder
of an area. The aim is a short session driven by specific questions, with
every answer landing in the repo the same day.

## Prepare (before talking to them)

1. Rank their single-author and majority-author paths by recent commits
   (the scan's concentration table, or
   `git log --author='<name>' --since=1.year --name-only --format= | sort | uniq -c | sort -rn`).
2. Run the newcomer walk on those paths first and note every guess and
   block.
3. Mine their commit messages, PR descriptions and code comments for the
   whys they already wrote down. Do not ask what history answers; it
   wastes the session and signals you did not look.
4. Draft the questions list: one line each, answerable in a sentence or
   two, grouped by stage. Send it ahead so they can check notes.

## Question bank

Pick what the walk left open; skip what the repo answers.

**Setup and access**
- Which accounts, keys or licences does working on this need, and who
  grants each now that you will not?
- Is anything on your machine (a CLI login, an SSH config, a local
  override, a cron job) that the work depends on?

**Change**
- Which parts are fragile, and what breaks when they are changed?
- Which conventions do you enforce in review that no tool checks?
- Is anything half-finished: a migration, a feature flag, a deprecation?

**Release**
- Walk through the last release: every command, every manual check.
- What is the rollback, and when did you last use it?
- Who else has the access to release today?

**Operate**
- What pages you, and what do you do first each time?
- For each unexplained constant (timeout, retry, batch size, threshold):
  why that value, and what happens either side of it?
- Which failures have you fixed more than once?

**Outside the code**
- Which vendors, partner teams or customers contact you directly about
  this, and who should they contact instead?
- Which recurring calendar events, reports or renewals (certificates,
  domains, licences) do you own?
- Where are notes, dashboards or docs that live outside the repo?

## Turn answers into repo artefacts

| Answer | Lands as |
|---|---|
| a release or recovery sequence | a task or script, plus a runbook entry that calls it |
| why a value is what it is | a comment on the constant citing the handover ("per <name>, <date>: …"), and a test if a boundary matters |
| an access path | the Access section and `.env.example` sources |
| a fragile area | a comment at the entry point, and a test that pins the fragile behaviour |
| a half-finished change | an issue with the remaining steps, linked from the code |
| a recurring obligation | an issue or calendar owned by a team, named in the runbook |
| something they cannot explain either | a question that stays open, labelled as unknown |

Record answers in the repo with attribution and date, because a cited
answer can be re-checked later while an unattributed one is just
asserted. Keep `BUS-FACTOR.md` current: strike questions as they are
answered and link the commit that encoded the answer.

## After they go

Re-run the newcomer walk with someone who was not in the handover, or a
fresh agent with only the repo. Anything they still have to guess was
not captured.
