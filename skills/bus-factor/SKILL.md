---
name: bus-factor
description: >-
  Raise a repository's bus factor so a newcomer can understand, run, change,
  release and operate it from the repo alone: walk the newcomer path, find
  knowledge held only by people, chat, wikis or one machine, measure
  single-author concentration in git, encode what the repo proves into
  tooling and docs, and turn what only people know into questions for them.
  Use when asked about bus factor, knowledge silos, tribal knowledge,
  onboarding, a handover or a maintainer leaving, or making a repo
  self-explanatory.
---

# Bus factor

A repo's bus factor is how many people could vanish before nobody can
move it forward. Raise it by moving knowledge out of heads, chat threads,
wikis and laptops into the repo, as tooling first and prose second, so
that a stranger with a clean checkout and the access the repo tells them
how to get can do real work without asking anyone.

The measure is the work, not the docs. A repo with a long README can
still fail a newcomer at step two, and a repo with a short one can pass
because its Taskfile, `.env.example` and CI say everything. So audit by
trying the work.

## Principles

1. **The newcomer walk is the test.** Every point where a stranger would
   have to guess, ask, or find something outside the repo is a finding.
   A finding records the step, what was missing, and the evidence.
2. **Executable beats written.** A pinned version, a task, a CI check, a
   test, an `.env.example` or a script fails loudly when it goes stale;
   prose drifts in silence. Encode knowledge in the most executable form
   that fits, and write prose only for what cannot run: purpose, why,
   who.
3. **Never invent knowledge.** Write only what the repo, its history or
   its behaviour proves, and cite the source (`git log` hash, file:line,
   test name). A plausible guessed "why" is worse than a gap, because
   readers trust it. What only a person knows becomes a question for
   that person, not a sentence in a doc.
4. **Point at access, never hold it.** Docs say where a secret lives (the
   vault path, the SSM parameter, the CI secret name) and which role
   grants access. They never hold a value, and "ask whoever set it
   up" is not a source.
5. **Fit the existing structure.** Add to the docs and entry files the
   repo already has, behind its existing routes. A new top-level doc per
   finding is sprawl that the next newcomer must also read.

## Workflow

1. **Scope and scan.** Default to the whole repo; narrow to an area when
   the user names one or a person's departure defines it. When the repo has
   git history or more than a handful of files, run
   `python3 <skill-dir>/scripts/scan_bus_factor.py <repo>` (add `--json`
   for machine use, `--since 2.years` to weigh recent work). It reports
   which knowledge-carrying files exist, per-path bus factor and holders,
   env vars read in code but documented nowhere, pointers to people,
   chat, wikis or personal paths, manual steps, and constants with no
   comment. Treat its output as leads to confirm, not findings.
2. **Walk the newcomer path.** Using only what the repo says, go through
   the stages in the table below in order. Run the safe commands (install,
   build, lint, test, run locally) rather than reading about them; never
   deploy, publish or touch shared infrastructure. Score each stage
   **pass** (the repo told you), **guess** (you inferred it from code; a
   human might not), or **blocked** (the answer is not in the repo).
3. **Mine history before asking anyone.** For every "why" gap (an odd
   constant, a pinned version, a workaround) search the history first:
   `git log -S'<literal>' --format='%h %an %s%n%b'`, `git log --follow
   <file>`, and PR or issue references in messages. A reason found there
   is derivable knowledge: encode it with its citation. Only what history
   cannot answer goes to a person.
4. **Find the concentration.** From the scan or `git shortlog -sn --
   <path>`, list the areas where one or two people hold most commits.
   Concentration alone is not a finding; concentration where the walk
   found guesses or blocks is the highest risk, and its top author is
   who the questions go to. Treat bot and agent authors as the human who
   directed and merged the work.
5. **Write `BUS-FACTOR.md`** at the repo root: the walk result per stage,
   the concentration summary, then one row per finding, most damaging
   first:

   `| # | stage | gap | evidence | impact | fix | source |`

   Impact: **blocked**, **guess**, or **slow** (findable, but only by
   reading code). Source: **repo** (derivable; cite where) or
   **person: <name or role>** (only a human can supply it). Close with
   **Questions for maintainers**, grouped by person, each question
   specific enough to answer in a sentence ("Why is the cache TTL 90
   seconds, and what breaks if it is shorter?", not "explain the
   cache"). Stop here when only an audit or a handover list was asked
   for.
6. **Fix the derivable gaps**, blocked first, one commit per stage so a
   reviewer can check each against the walk. Choose the most executable
   home that fits:

   | Knowledge | Prefer | Over |
   |---|---|---|
   | toolchain versions | a pin file (`mise.toml`, `.python-version`, `.nvmrc`) | "requires Python 3.11+" in prose |
   | a multi-step ritual | a task or Make target, its doc one line | a numbered list in a README |
   | config and env vars | `.env.example` with each var, a one-line meaning and its source | a table nobody updates |
   | a constraint on code | a test named for the rule, plus a cited comment | a wiki page |
   | a decision | an ADR or a cited comment, marked "reconstructed from <hash>" | an unattributed paragraph |
   | a machine-specific path | a repo-relative path or a variable | a note to change it |
   | ownership | `CODEOWNERS` with owners the user confirms | names guessed from history |

   Never fill a **person** row yourself: leave it in the questions list.
   Propose `CODEOWNERS` entries from history but write them only once the
   user confirms them, because ownership is a commitment, not a fact.
7. **Verify by walking again**, ideally in a fresh context: a subagent
   given only the repo and the stage list, told not to read
   `BUS-FACTOR.md`. Report before and after per stage, gaps closed, and
   questions still open. Run the repo's own checks and tests last.

## The newcomer path

| Stage | A newcomer must be able to answer from the repo |
|---|---|
| purpose | what this is, who uses it, what is out of scope, and which systems it talks to (a C4 context view) |
| setup | toolchain and versions, dependencies, how to get config and secrets access |
| build and test | one command each, and what green looks like |
| change | where things live and how the containers fit (a C4 container view), conventions (branching, commits, style) and how they are enforced, how review works |
| release | how a change reaches users, who can do it, how to roll back |
| operate | config per environment, where secrets live, logs and alerts, known failure modes and their fix |
| ownership | who owns each area and how to reach them, as a role or team where possible |

Open [references/knowledge-areas.md](references/knowledge-areas.md) when
a stage needs more than the table: what "answered" looks like per stage,
signals a stage is failing, and examples of good encodings.

## Handover from a person

When someone is leaving, or the user wants to capture what one person
knows, the history tells you what to ask. Rank that person's
single-author areas by recent commits, run the walk on those first, and
produce the questions list for them before anything else; an hour of
their time on specific questions beats a week of reverse engineering
after they go. Open [references/handover.md](references/handover.md) when
planning the interview: question bank per stage, how to turn answers into
repo artefacts, and what to collect that is not code (accounts, keys,
vendor contacts, calendars).

## When not to use

- Docs that exist but are wrong or duplicated: `repo-consistency-checker`.
- Docs that are true but verbose: `repo-declutter`.
- Where docs live and what agents load: `repo-optimization`. Run this
  skill first to find what is missing, that one to place it cheaply.
- Generated, vendored or third-party code: its knowledge lives upstream.
- For all four questions at once, `repo-health` runs this skill with its
  neighbours and owns the branch, commits, audit location and PR.

## References

- [references/knowledge-areas.md](references/knowledge-areas.md): per
  stage, what answered looks like, failure signals and good encodings;
  open when a stage needs judgement beyond the table.
- [references/handover.md](references/handover.md): interview plan,
  question bank and artefact mapping; open when a person is leaving or
  the user wants knowledge captured from someone.
- `scripts/scan_bus_factor.py`: stdlib scan behind step 1. Run it; open it
  only if it errors or a lead needs explaining.
