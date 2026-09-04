---
name: goldratt-4-questions
description: >-
  Evaluate whether a technology, tool, or platform is worth adopting using
  Goldratt's four questions on the value of new technology: what is its
  power, what limitation does it diminish, what rules accommodated that
  limitation, and what rules should replace them. Use when the user asks
  "should we adopt/use/buy X", wants to evaluate, compare, or justify a
  technology choice, mentions Goldratt or the four questions, wants an ADR
  or tech-radar assessment written, is challenging a shiny-tech proposal
  ("everyone's using X"), or asks why an adopted tool isn't delivering the
  promised value.
---

# Goldratt's Four Questions

A new technology only creates value when it diminishes a limitation you
actually have — and even then, only if you also change the rules, habits,
and processes that grew up around that limitation. Adopt the tech but keep
the old rules and you pay the cost without collecting the benefit. This
skill walks a technology decision through Goldratt's four questions until
each has a concrete, testable answer, then delivers a verdict.

The four questions, in order:

1. **What is the power of the technology?** What can it do?
2. **What limitation does it diminish?** What previously couldn't be done,
   or was expensive/slow/risky to do?
3. **What rules helped us accommodate the limitation?** The processes,
   habits, and structures that exist *because* of the limitation.
4. **What rules should we use now?** What replaces those rules once the
   limitation is gone?

The order matters: each answer is interrogated against the one before it.
Do not let the conversation skip to question 4 enthusiasm ("we could do X!")
before questions 2 and 3 are pinned down.

## Step 1 — establish the mode

Work out which situation this is and say which you're in:

- **Evaluation** — a technology is being considered. Interview the user
  through the four questions, a few questions per turn.
- **Review** — a proposal, ADR draft, or vendor pitch already exists. Map
  its claims onto the four questions first, then interview only about the
  gaps — usually questions 3 and 4, which proposals almost always omit.
- **Post-mortem** — something was adopted and isn't paying off. Run the
  questions retrospectively; the failure is nearly always found at
  question 4 (old rules kept alive alongside the new technology).

## Step 2 — walk the questions

Maintain a running answer sheet — the four questions with the current best
answer, plus an **Open** list for what nobody could answer — and show it
back after each round. Ask at most three questions per turn. For each
question, push until the answer passes its test:

**Q1 — Power.** Distinguish power from features. A feature list ("it has
dashboards, an API, SSO") is not an answer; power is the one or two things
it makes possible or radically cheaper. Test: can the user state the power
in a sentence without naming a feature?

**Q2 — Limitation diminished.** The crux. The limitation must be one *this
team actually suffers from*, stated with evidence: where does it bite, how
often, what does it cost? "We might need it at scale" is a limitation they
don't have yet — park it. If nobody can name a real limitation, stop and
say so plainly: the proposal is fashion, not value, and the honest verdict
is "don't adopt (yet)".

**Q3 — Old rules.** These are usually invisible because they feel like
"how work is done", not workarounds. Probe with: what do we do *because*
of this limitation? What would look absurd to someone who never had the
limitation? Batch sizes, approval gates, manual checks, coordination
meetings, defensive copies, "always email the team before X" are all rules.
If no accommodating rules surface, be suspicious of Q2 — a real limitation
always leaves scar tissue.

**Q4 — New rules.** For each old rule, decide: retire it, replace it, or
keep it (some rules serve other purposes). The danger answer is "we'll
adopt the tech and keep working the same way" — name it as the
cost-without-benefit trap. Each new rule must name who changes behaviour
and what they stop doing; a rule nobody stops anything for isn't a change.

Worked in miniature — adopting data contracts on a pipeline:

- **Power**: machine-checkable agreement on data shape and quality.
- **Limitation**: consumers can't trust upstream data; breakage found in
  production (~2 incidents/month, each costing a day).
- **Old rules**: consumers defensively re-validate everything; schema
  changes go through a change-advisory email thread; releases batched
  monthly to limit blast radius.
- **New rules**: contract check gates the producer's CI; consumers drop
  their duplicate validation; schema changes ship any time the contract
  passes — the email thread and the monthly batch are retired.

Without the last line, the team would run contracts *and* the email
thread *and* the defensive validation: pure added cost.

## Step 3 — deliver the verdict

Close with a short written assessment: the four answers, the open
questions, and one of four verdicts —

- **Adopt** — with the new rules (Q4) listed as the adoption work, since
  they *are* the adoption; the install is the easy part.
- **Adopt when** — the limitation is real but not yet biting; name the
  trigger condition that reopens the decision.
- **Spike** — a question (usually Q2's evidence or Q1's power claim) can
  only be answered by trying it; scope the spike to answer exactly that.
- **Don't adopt** — no real limitation, or the new rules are ones the
  org won't accept; say which.

If the user wants the assessment as a formal ADR, or the verdict is
"adopt" and they want to plan the rollout (Goldratt's extended fifth and
sixth questions cover this), open
[references/adoption-and-adr.md](references/adoption-and-adr.md).

## Step 4 — hand over

The assessment is the deliverable; write it to a file when it needs to
outlive the conversation (e.g. `docs/decisions/`). Downstream, if the
matching skills are available: the Q4 new rules and rollout become units
of delivery for `work-breakdown`, and requirements for what gets built
around the technology go to `requirements-to-gherkin`.

## References

- [references/adoption-and-adr.md](references/adoption-and-adr.md) — open
  only when writing a formal ADR or planning an adoption: the extended
  fifth and sixth questions, an ADR template shaped by the four questions,
  and a full worked example.
