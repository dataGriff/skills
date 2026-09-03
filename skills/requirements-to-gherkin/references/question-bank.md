# Elicitation question bank

Probes organised by category, for when an area of the discovery board
feels thin and the obvious questions are exhausted. Pick the few that fit;
never run a category as a checklist — every question spent on a low-stakes
area is attention taken from a rule that matters.

Phrase probes as concrete scenarios where you can: "what happens when
Alice, who is not an admin, tries X?" out-performs "what are the
permission requirements?" every time.

## Actors and permissions

- Who triggers this? Who else is allowed to? Who must never be able to?
- Does anyone act on someone's behalf (support agent, admin, parent,
  delegate)? Do the rules change when they do?
- Is there a non-human actor — a scheduled job, another system, a webhook?
  What happens when it and a human act at the same time?
- Who finds out this happened, other than the actor? How?

## Triggers and timing

- What exactly starts this — a user action, a clock, an external event?
- Can it happen twice? Concurrently? What should the second occurrence do —
  fail, queue, merge, replace?
- What must already be true before it can start? What state blocks it?
- Is there a deadline, a window, an expiry? Which clock and timezone
  defines it, and what happens exactly on the boundary?

## Outcomes

- What does the actor observe when it works? Immediately, or later?
- What does the actor observe when it's rejected? Is the reason disclosed,
  or deliberately withheld (security, privacy)?
- What changes in the world beyond the screen — money moves, email sent,
  stock reserved, audit record written?
- Can it be undone? By whom, until when, and what does undoing undo?

## Data and boundaries

- For each input: what's the smallest and largest acceptable value? What
  happens one step beyond each edge?
- What's genuinely optional, and what does the system do when an optional
  thing is absent?
- Where does the data come from — user-typed, imported, computed? Who
  fixes it when it's wrong?
- Money: which currency, who rounds, and in whose favour? Dates: which
  timezone, and what about daylight-saving transitions?
- What already exists? Migrations and backfills for existing records are
  requirements too.

## Lifecycle and states

- Draw the states this thing moves through. Which transitions are allowed,
  and who may make each one?
- What may happen to an item in each state — can a shipped order be
  edited, a closed account be reopened?
- Is there deletion? Soft or hard, who may, and what happens to dependent
  records?

## Failure and the outside world

- Which parts depend on another system? What should the user experience
  when that system is down or slow — block, retry, degrade?
- What's the cost of this going wrong quietly vs. loudly? Who needs to be
  alerted?

## Non-functional (only when stakes justify it)

- How many of these per day/hour at peak? What response time counts as
  broken, measured from where?
- Who must *not* be able to see this data? How long is it kept, and is
  anyone legally required to delete or retain it?
- Does this need to work on mobile / offline / in other languages?

## Prioritisation and scope

- If only one of these rules shipped next week, which one? Which rule,
  if wrong, costs the most?
- What is explicitly *not* part of this? Get it said and park it on the
  board's Out-of-scope list.
- Is there an existing behaviour this replaces? What must keep working
  unchanged?
