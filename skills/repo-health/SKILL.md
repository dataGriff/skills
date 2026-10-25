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
- **Audits are the PR body.** Each phase writes its audit as its own
  section of `.repo-health/PR.md`, an untracked directory at the repo root
  that ignores itself (step 1 creates it with a `.gitignore` containing
  `*`; agents cannot write under `.git/`). Never `BUS-FACTOR.md` or
  `DECLUTTER-AUDIT.md` at the root, and nothing is written twice. Once
  the PR is open, delete the directory; the body lives in the PR.
- **Each phase keeps its own skill's gates.** What a sub-skill applies on
  its own, it applies here, including the files it creates (a pin file,
  `.env.example`, a rule-named test, a Taskfile, hooks, a CI wrapper)
  when its own conditions hold. Those conditions are the guard against
  over-treatment; a second blanket "propose only" on top turns a needed
  fix into a suggestion. What a sub-skill defers to a person stays a
  judgment call here: bus-factor's person-sourced rows and CODEOWNERS,
  consistency's "possible bug", declutter's "verify" rows and public
  renames, GitHub settings without admin. Do not stop after an audit; the
  PR is the review point.
- **The pass verifies once.** Its final check run replaces each
  sub-skill's own verification walk; do not spawn fresh-context re-walks
  per phase.

## Workflow

1. **Baseline.** Confirm a clean tree and the default branch; create the
   branch and `.repo-health/` with its self-ignoring `.gitignore`. Run the repo's
   checks and tests once and record the result in the PR body: a red
   baseline is reported, not fixed, every phase keeps the failing set
   unchanged, and declutter then touches docs and comments only. Record
   `gh` capability once: `gh auth status` fails for any reason → none;
   otherwise `gh api repos/{owner}/{repo} --jq .permissions.admin` → admin
   or write.
2. **Triage.** When `python3` is available, run
   `python3 <this skill's dir>/scripts/scan_repo_health.py <repo>` and
   take its table as the plan, however small the repo: a hand triage
   skips the checks it does not think of, the unrouted doc above all.
   Fill the table by hand from the signals below only when it cannot
   run. Its `--json` output carries every sibling
   scanner's leads, so the phases take their leads from it instead of
   re-running their own scans; it skips `fixtures/` and `evals/`
   directories, whose flaws are deliberate. Signals are leads, and some are false
   (a URL pattern read as a path); a phase that finds only noise commits
   nothing and says so. Override a verdict only with a reason that goes
   in the PR. All four skip: reply with the table, open nothing.

   | Phase | Runs when the repo shows |
   |---|---|
   | bus-factor | env vars read in code but documented nowhere; pointers to a person, chat, wiki or personal path; no pin file or documented setup; a path with one holder; more than one deployable and no C4 view of them |
   | consistency | a broken reference or undefined command; a duplicated paragraph; commented-out code; TODO/FIXME markers |
   | declutter | docs carrying history or hedged prose; files with banners, attributions or dense comments |
   | optimization | no auto-loading entry file, or one over budget; a doc nothing routes to; commands in more than one home; no CI |

3. **Phases, in order, only those that run.** Load the sub-skill (a
   skipped phase's skill is never loaded): in Claude Code the Skill tool
   by name, otherwise read `<name>/SKILL.md` from the directory beside
   this skill's. Pass it the scope the user gave (whole repo by default)
   and the contract above. Run the repo's checks once at the end of the
   phase, then commit, writing the counts into the message last.
   - *bus-factor*: write each gap into the most executable home its fix
     table names, creating the file when it is missing (C4 views go in
     `docs/architecture.md`, derived from compose, IaC, entry points and
     client code). Never create AGENTS.md; optimization places content
     last. Questions for people go to the audit, never answered by
     guessing.
   - *consistency*: fix drift to the code's truth, delete dead code,
     commented-out code and finished TODOs, collapse duplicated facts to
     one home. Verify a numeric claim only in a file this phase already
     edits; otherwise list it as "verify" in the PR.
   - *declutter*: trim prose and comments that survive consistency;
     history goes into the commit body. Protected content stays.
   - *optimization*: routes-only when an entry file exists and fits (a
     route names its trigger and says "read"; "see" is a mention, not a
     route); a minimal AGENTS.md (plus `CLAUDE.md` = `@AGENTS.md`) when
     none does;
     fan-out only when the entry file is over budget. Its steps 5–7
     (runner, hooks, CI, guardrail checks) run when that skill's own
     conditions hold and are skipped otherwise. With admin, run its
     `github-settings.sh`; otherwise put the command under judgment calls.
4. **Verify.** Run the checks and tests a final time; re-run the triage
   scan for before/after signal counts. Anything this turns up is fixed
   inside the owning phase's commit (`git commit --fixup` and an
   autosquash rebase; the branch is unpushed), never as a fifth commit.
5. **Deliver.** The PR body is `.repo-health/PR.md`, in this order:
   Summary (the triage table with ran/skipped and the commit per phase);
   Bus factor (stage walk before/after, Questions for maintainers);
   Consistency (severity table, coverage note); Declutter (findings,
   Protected — kept, deferred); Optimization (outcome chosen, before/after
   tokens and reads, GitHub settings applied or the command to run);
   Judgment calls (one list that points at the rows above, `file:line`
   each, not a repeat of them); Checks (baseline and final). Open it with
   `gh pr create --draft --title "repo-health: <n> of 4 phases" --body-file`.
   When `gh` is unavailable, or the repo has no remote, leave the branch
   and the file, and print that command in the reply.

## Who owns which finding

Two phases often detect the same thing. The owner fixes it; later phases
do not look for it again.

| Finding | Owner | Later phases |
|---|---|---|
| commented-out code, finished or ownerless TODOs | consistency | declutter's comment category covers restating comments, banners, attributions only |
| duplicated facts or paragraphs | consistency | declutter trims verbosity, never merges duplicates |
| broken links | consistency | optimization adds routes; it does not re-check links |
| a doc nothing routes to | optimization, with a route | consistency deletes it only when its content is stale or already lives elsewhere |
| missing setup, deploy or "why" knowledge | bus-factor, in the most executable home | optimization places and budgets it last |
| env vars and their sources | bus-factor, in `.env.example` | consistency keeps docs pointing at it, never a second table |
| system shape (C4 context and container views) | bus-factor, in `docs/architecture.md` | consistency checks every box against a deployable or client; optimization routes to it |
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
