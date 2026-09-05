# Adoption planning and ADR format

Open this only when the four-question assessment is done and the user
wants a formal ADR, or the verdict is "adopt" and the rollout needs
planning.

## The extended questions (5 and 6)

Goldratt's fuller sequence (from *Necessary But Not Sufficient* and his
later "Strategy & Tactics" work) adds two questions once the new rules
are known:

**Q5 — In light of the new rules, what changes are required to the
technology?** The out-of-the-box configuration assumes someone else's
rules. Walk each Q4 new rule and ask what the tool must be configured,
integrated, or extended to do so the rule is *enforced by the system*
rather than by memory. A new rule that relies on everyone remembering it
reverts to the old rule within a quarter. Examples: the contract check
must gate CI (not sit in a dashboard nobody opens); the old path must be
switched off, not left as a fallback.

**Q6 — How do we cause the change?** Adoption is a change-management
problem wearing a technology costume. Plan, per affected group:

- **Who loses what.** Every retired rule is someone's routine, and
  sometimes someone's role. Name them; they are the resistance if
  unaddressed and the champions if involved early.
- **Sequence.** Pilot on one team/pipeline/service where the limitation
  bites hardest — the pain makes the value visible. Expand only after the
  pilot has retired its old rules, not merely installed the tool.
- **Kill criteria.** What observed result within what timeframe means
  stop and revert? Deciding this before rollout keeps the decision
  honest.
- **The old rule's funeral.** Schedule the explicit retirement of each
  old rule (delete the check, cancel the meeting, close the mailbox).
  Un-retired old rules are how adoptions silently fail.

Q5 and Q6 answers slice naturally into units of delivery — hand them to
`work-breakdown` if available.

## ADR template

Shape the ADR so the four questions are visible in it — that is what
makes it defensible later. Use the repo's existing ADR format if one
exists and fold these sections into it; otherwise:

```markdown
# ADR-NNN: Adopt <technology> for <purpose>

## Status
Proposed | Accepted | Superseded by ADR-MMM

## Context (the limitation)
The limitation we suffer from, with evidence: where it bites, how
often, what it costs. [Goldratt Q2 — if this section is thin, the
ADR is not ready.]

## Decision
Adopt <technology>: <its power in one or two sentences, Q1>.

## Rules we retire or replace
| Old rule (existed because of the limitation) | New rule | Who changes |
| --- | --- | --- |
| ... | ... | ... |
[Q3 → Q4. An empty table means cost without benefit — do not accept
the ADR with this table empty.]

## Required changes to the technology
Configuration/integration work so the new rules are enforced by the
system, not by memory. [Q5]

## Rollout
Pilot scope, expansion criteria, kill criteria, and the scheduled
retirement date of each old rule. [Q6]

## Consequences
What gets better, what gets worse or riskier, and the open questions
with owners.
```

## Worked example — adopting a message broker

A team runs nightly batch file transfers between six services and is
considering Kafka.

- **Q1 — Power**: durable, ordered, replayable event streams that many
  consumers read independently, near-real-time.
- **Q2 — Limitation**: integrations are point-to-point file drops;
  adding a consumer means asking the producer for a new export (2–4
  weeks lead time, happens ~monthly); data is up to 24h stale, which
  loses the fraud team an estimated £15k/month. Evidence is concrete —
  the limitation is real.
- **Q3 — Old rules**: nightly batch windows and the freeze around them;
  a "request a new export" form and its approval queue; each consumer
  keeps a defensive local copy of everything it receives; reconciliation
  reports every morning to detect missed files.
- **Q4 — New rules**: producers publish once to a topic and never build
  bespoke exports (the request form is retired); consumers self-serve by
  subscribing (approval queue retired); replay replaces local defensive
  copies; reconciliation reports retired for migrated flows; schema
  changes governed by a contract check on the topic instead of the
  freeze window.
- **Verdict**: adopt — but the adoption work is the Q4 list, and the
  batch window must be *removed* for migrated flows, not kept "just in
  case".
- **Q5**: schema registry with compatibility checks wired into producer
  CI; retention long enough that replay genuinely replaces local copies;
  the SFTP endpoints for migrated flows decommissioned.
- **Q6**: pilot with the fraud flow (worst pain, clearest value);
  expansion criterion: fraud flow live 30 days with its reconciliation
  report retired; kill criterion: if operating burden exceeds one
  engineer-day/week after 60 days, revert and reassess a managed
  service. Old-rule funerals scheduled per migrated flow.

The tell in this example: if the team had kept the nightly batch and the
reconciliation reports "for safety", they would be operating Kafka *and*
the old system — the cost-without-benefit trap the four questions exist
to catch.
