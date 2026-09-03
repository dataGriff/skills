---
name: requirements-to-gherkin
description: >-
  Gather, structure, and pin down software requirements, then convert them
  into Gherkin acceptance criteria ready to code from. Use when the user has
  a vague idea, feature request, user story, meeting notes, or stakeholder
  transcript and needs it turned into concrete, testable requirements; wants
  help interviewing stakeholders or preparing questions to take to them;
  mentions requirements gathering, elicitation, discovery, example mapping,
  a three amigos session, or acceptance criteria; or says things like "help
  me work out what to build", "what should I ask the business", "turn these
  notes into scenarios", or "I can't get clear requirements from people".
---

# Requirements to Gherkin

Requirements fail in two ways: they stay vague ("the system should handle
refunds"), or they get invented by whoever writes them down. This skill's
job is to close the gap between what stakeholders say and a set of concrete
rules with examples — then express those as Gherkin. The core move
throughout: **ask for examples, not opinions.** "Should refunds be
allowed?" gets a vague yes; "Alice bought a £30 jumper 40 days ago and
wants her money back — what happens?" gets a rule.

## Step 1 — establish the mode

Work out which situation this is and say which you're in:

- **Live elicitation** — the user answers questions themselves (or is
  relaying to a stakeholder). Interview them, a few questions per turn.
- **Session prep** — the user is going to talk to people and wants to walk
  in with the right questions. Produce a tailored question set and a
  capture structure they can fill in during the conversation.
- **Raw material** — the user already has notes, a transcript, tickets, or
  a story with woolly acceptance criteria. Mine it first, then interview
  only about the gaps.

All three converge on the same discovery board (step 2) and the same
conversion (step 4).

## Step 2 — build the discovery board

Maintain one running structure and show it back after every round of
answers, so the user always sees what's settled and what's open:

- **Story** — one sentence: who wants this, what they do, why it matters.
  If you can't fill this in, ask for it before anything else.
- **Rules** — the business constraints, each stated as a decidable
  sentence ("Refunds are allowed within 30 days of delivery"), not a
  topic ("refund window").
- **Examples** — concrete cases under each rule, with named actors and
  real values ("Alice, £30 jumper, delivered 29 days ago → refunded").
- **Questions** — anything unknown, ambiguous, or contradictory, each
  attributed to who can answer it. This column is the deliverable the
  user takes back to their stakeholders; never quietly resolve an entry
  by guessing.
- **Out of scope** — things explicitly parked, so they stop resurfacing.

This is example mapping in text form. If the user is facilitating a live
group session and wants to run the card-based version with stakeholders in
the room, open [references/example-mapping.md](references/example-mapping.md).

Show the board in chat after each round, but when the work will span
sessions — questions going out to stakeholders and answers coming back
later — the board's home is a file (e.g. `discovery.md` next to the
feature files it will produce), updated as you go. On resuming, read that
file first, fold new answers into it, and regenerate whatever scenarios
they touch. A board that lives only in the conversation dies with it.

## Step 3 — interrogate until rules are decidable

Ask **at most three questions per turn**, most important first — a wall of
questions gets skimmed and half-answered. Prefer a concrete scenario over
an abstract question, and a closed probe over an open one once a rule is
taking shape.

Chase these signals whenever they appear in what people say or write:

- **Vague qualifiers** — "quickly", "user-friendly", "secure", "robust",
  "handle". Pin each to an observable outcome or a number: "quickly" →
  "within how many seconds, measured where?"
- **Missing actor** — passive voice ("the order is approved") hides who
  acts. Ask who, and whether anyone else may.
- **Missing outcome** — "the system validates the input" says nothing
  about what a user sees on failure. Ask what the actor observes, in both
  directions.
- **Absolutes** — "always", "never", "all users". Probe for the
  exception: "never? what about an admin / a refund / a leap year?"
- **"Etc." and "and/or"** — enumerate the list or split the rule.
- **Boundaries** — every number in a rule has edges. 30-day window: what
  happens on day 30? Day 31? Which timezone starts the clock?
- **The unhappy paths** — for each rule, get at least one example of the
  rule *rejecting* something. Stakeholders volunteer happy paths;
  rejections are where the real decisions live.

A rule is done when it has a normal example, a boundary example, and a
rejection example, and none of them depends on an open question. For a
fuller probe list organised by category (actors, triggers, data,
lifecycle, non-functional), open
[references/question-bank.md](references/question-bank.md) — useful when
an area feels thin and you can't see what to ask next.

Know when to stop: when new questions stop changing the rules, or only
low-stakes questions remain, say so and move to conversion. Perfect
coverage is not the goal; a small set of decidable rules plus an honest
Questions list beats an exhaustive interview.

## Step 4 — convert to Gherkin

Convert only rules whose examples are decidable; everything else stays on
the Questions list. If the `gherkin-feature-authoring` skill is available,
apply it for authoring style. Either way the mapping is:

- The **Story** becomes the `Feature:` narrative.
- Each **Rule** becomes a `Rule:` block, worded as on the board.
- Each **Example** becomes one `Scenario:` — Given the context, exactly
  one When for the event, Then an outcome the actor can observe. Keep the
  board's named actors and real values; no UI mechanics ("Alice requests
  a refund", never "clicks the Refund button").
- Each open **Question** that blocks a scenario appears in the feature
  file as a comment right where the answer belongs, e.g.
  `# OPEN: does the 30-day window use the customer's timezone? (asked Priya)`
  — with the most plausible scenario written beneath it, clearly marked
  as assumed. Never present an invented outcome as agreed.

```gherkin
Feature: Refunds
  As a shopper, I want a refund on unwanted items
  so that buying online is risk-free.

  Rule: Refunds are allowed within 30 days of delivery

    Scenario: Refund inside the window
      Given Alice's jumper was delivered 29 days ago
      When Alice requests a refund
      Then her £30 payment is returned

    Scenario: Refund on the last day of the window
      Given Alice's jumper was delivered 30 days ago
      # OPEN: is day 30 in or out? Assumed in. (asked Priya)
      When Alice requests a refund
      Then her £30 payment is returned

    Scenario: Refund after the window
      Given Alice's jumper was delivered 31 days ago
      When Alice requests a refund
      Then the refund is declined
      And she is told the 30-day window has passed
```

Gherkin is not the only artefact the board can feed. Answers about data
shape, ranges, quality, retention, or SLAs, and about operations, events
and payloads, are the raw material of data contracts and interface specs:
when the deliverable includes one, hand the relevant rules and examples to
the matching authoring skill if available (`datacontract-cli`,
`odcs-authoring`, `openapi-authoring`, `asyncapi-authoring`) — the board's
concrete examples double as example records and payloads. Behaviour still
goes to Gherkin; shape and obligation go to the contract.

## Step 5 — hand over

Deliver both artefacts, not just the feature file: the discovery board is
what goes back to stakeholders (especially its Questions column), the
`.feature` file is what goes to the codebase. Offer to update both when
answers come back — an answered question turns its assumed scenario into
an agreed one, or rewrites it.
