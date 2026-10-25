---
name: repo-health
description: >-
  Run a whole repo-health pass in one go: triage with one scan, then apply
  bus-factor, repo-consistency-checker, repo-declutter and
  repo-optimization in order, only the phases the repo needs, on one branch
  with one commit per phase and one draft PR carrying every audit and the
  judgment calls left for a human. Use when asked to get a repo all right,
  healthy, tidy, in shape, or ready for handover or adoption, to run the
  repo-health skills together, or for a full pass over docs, comments and
  agent setup; for one symptom use the single skill that names it.
---

# Repo health: the full pass

Four skills each answer one question about a repository, in an order
where each answer changes what the next one sees: is knowledge
**missing** (`bus-factor`), is what is written **true and said once**
(`repo-consistency-checker`), is it **longer than it needs to be**
(`repo-declutter`), can an agent **find it cheaply** (`repo-optimization`).
This skill runs them as one pass and owns everything they do not agree on:
the branch, the commits, where audits go, and the PR.

A full pass costs four skills' worth of reading, and the measured risk in
this family is over-treatment: restructuring a repo that was already fine
made every later task dearer. So triage decides which phases earn their
cost, and a healthy repo gets a table and no branch.

## Contract

Every phase follows its own skill's workflow, with these overrides:

- **One branch**, `repo-health/<YYYY-MM-DD>`, from the default branch, on
  a clean tree (stop and ask if it is not clean). Never push to the
  default branch; the pass configures the host to refuse that anyway.
- **One commit per phase**, conventional format
  `chore(bus-factor|consistency|declutter|optimization): <one line>`, with
  the sub-skill's own granularity (stages, logical groups, categories) as
  bullets with counts in the body. Not a commit per category: a reviewer
  reads one PR, not twelve commits.
- **Audits go inside `.git/`**, at `$(git rev-parse --git-dir)/repo-health/<phase>.md`,
  never `BUS-FACTOR.md` or `DECLUTTER-AUDIT.md` at the root. Nothing
  lands at the repo root that is not the repo's own content; the PR body
  carries the audits.
- **Mechanical fixes are applied; judgment calls are listed.** Mechanical:
  the sub-skill's fix table says what to write and the evidence is in the
  repo (drift to code truth, dead code, a broken link, an env var into
  `.env.example`, history into a commit body, a route line,
  `CLAUDE.md = @AGENTS.md`). Judgment: anything the sub-skill already
  defers to a person (bus-factor's person-sourced rows and CODEOWNERS,
  consistency's "possible bug", declutter's "verify" rows and public
  renames, optimization's build or fan-out beyond routes-only, GitHub
  settings without admin). Do not stop after an audit; the PR is the
  review point.

## Workflow

1. **Baseline.** Confirm a clean tree and the default branch; create the
   branch. Run the repo's checks and tests once and record the result (a
   failing suite means declutter touches docs and comments only). Record
   `gh` capability once: `gh auth status` fails for any reason → none;
   otherwise `gh api repos/{owner}/{repo} --jq .permissions.admin` → admin
   or write.
2. **Triage.** When the repo has git history or more than a handful of
   files, run `python3 <this skill's dir>/scripts/scan_repo_health.py <repo>`
   and take its table as the plan; for a tiny repo, fill the table by
   hand from the signals below. Override a verdict only with a reason that
   goes in the PR. All four skip: reply with the table, open nothing.

   | Phase | Runs when the repo shows |
   |---|---|
   | bus-factor | env vars read in code but documented nowhere; pointers to a person, chat, wiki or personal path; no pin file or documented setup; a path with one holder |
   | consistency | a broken reference or undefined command; a duplicated paragraph; an orphan doc; commented-out code; TODO/FIXME markers |
   | declutter | docs carrying history or hedged prose; files with banners, attributions or dense comments |
   | optimization | no auto-loading entry file, or one over budget; a doc nothing routes to; commands in more than one home; no CI |

3. **Phases, in order, only those that run.** Load the sub-skill: in
   Claude Code the Skill tool by name, otherwise read `<name>/SKILL.md`
   from the directory beside this skill's. Pass it the scope the user
   gave (whole repo by default) and the contract above. Run the repo's
   checks once at the end of the phase, then commit.
   - *bus-factor*: write knowledge into docs that exist; do not create
     AGENTS.md or `docs/` (optimization places content last). Questions
     for people go to the audit, never answered by guessing.
   - *consistency*: fix drift to the code's truth, delete dead code,
     commented-out code and finished TODOs, collapse duplicated facts to
     one home. Verify numeric claims only when another signal fires on
     the same file; otherwise list them as "verify" in the PR.
   - *declutter*: trim prose and comments that survive consistency;
     history goes into the commit body. Protected content stays.
   - *optimization*: decide routes-only, build or fan-out from what the
     earlier phases left; wire the runner, hooks and CI only when its own
     triggers hold; with admin, run its `github-settings.sh`, otherwise
     put the command under judgment calls.
4. **Verify.** Run the checks and tests a final time; re-run the triage
   scan for before/after signal counts.
5. **Deliver.** Assemble the PR body in this order: Summary (the triage
   table with ran/skipped and the commit per phase); Bus factor (stage
   walk before/after, Questions for maintainers); Consistency (severity
   table, coverage note); Declutter (findings, Protected — kept, deferred);
   Optimization (outcome chosen, before/after tokens and reads, GitHub
   settings applied or the command to run); Judgment calls (one list,
   `file:line` each); Checks (baseline and final). Open it with
   `gh pr create --draft --title "repo-health: <n> of 4 phases" --body-file`.
   Without `gh` or a remote: leave the branch, write the body to
   `.git/repo-health/PR.md`, and print that command in the reply.

## Who owns which finding

Two phases often detect the same thing. The owner fixes it; later phases
do not look for it again.

| Finding | Owner | Later phases |
|---|---|---|
| commented-out code, finished or ownerless TODOs | consistency | declutter's comment category covers restating comments, banners, attributions only |
| duplicated facts or paragraphs | consistency | declutter trims verbosity, never merges duplicates |
| broken links, orphan docs | consistency | optimization adds routes; it does not re-check links |
| missing setup, deploy or "why" knowledge | bus-factor, into existing docs | optimization places and budgets it last |
| README and AGENTS.md | content edits in phases 1–3 | shrinking, placement and the `@AGENTS.md` include in phase 4 |
| numeric claims | consistency, only alongside another signal | listed as "verify" in the PR otherwise |

## When not to use

- One symptom: run the single skill that names it (the catalog's symptom
  table), on the scope that symptom has.
- An audit or handover list with no changes: `bus-factor` alone.
- One doc that reads badly: `repo-declutter` on that doc.
- A PR diff after a refactor or rename: `repo-consistency-checker` on the
  files it touched.

## References

- `scripts/scan_repo_health.py` — the triage. Run it; open it only if it
  errors or you need to see a threshold.
