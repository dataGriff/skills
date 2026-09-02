# Gherkin style: declarative scenarios that earn their keep

How to write scenarios worth automating, and how to spot the ones that
aren't. Load this when writing more than a trivial scenario, when reviewing
feature files, or when rewriting scripts that grew out of manual test cases.

## Contents

- [BRIEF](#brief)
- [Declarative over imperative](#declarative-over-imperative)
- [Naming](#naming)
- [Tense, person, and voice](#tense-person-and-voice)
- [Step reuse and automation cost](#step-reuse-and-automation-cost)
- [Anti-pattern catalogue](#anti-pattern-catalogue)
- [Review checklist](#review-checklist)

## BRIEF

Five properties every scenario should have (Rose & Nagy's mnemonic):

- **B**usiness language — words the domain expert uses, no test or
  implementation jargon.
- **R**eal data — concrete names and values ("Alice", "£80"), which expose
  wrong assumptions the way `<user>` and `<amount>` never do.
- **I**ntention revealing — says what behaviour matters and why, not how
  the system is driven.
- **E**ssential — every line changes the outcome; anything that could be
  deleted without changing what the scenario proves, delete.
- **F**ocused — one scenario, one rule, one example of it.

## Declarative over imperative

The single most common failure. Imperative scenarios script the interface;
declarative scenarios state the behaviour:

```gherkin
# Imperative — brittle, unreadable, wrong altitude
Scenario: Login
  Given I open "https://app.example.com/login"
  When I type "alice@example.com" into the "email" field
  And I type "s3cret!" into the "password" field
  And I click the "Log in" button
  Then I see the text "Welcome back"

# Declarative — survives any UI redesign
Scenario: Registered user logs in
  Given Alice has a registered account
  When she logs in with valid credentials
  Then she sees her personal dashboard
```

Clicks, selectors, URLs, field names, and navigation belong in step
definitions. The test of altitude: would the scenario still be true if the
product shipped the same behaviour as a voice interface? If not, it's
describing the UI, not the behaviour. (Exception: a feature *about* the UI
itself — a design system's component spec — may legitimately mention UI
elements; that is the rare case, not the default.)

## Naming

- **Feature**: the capability, noun-phrase — `Account withdrawal`, not
  `Withdrawal tests`, `ATM screen`, or `JIRA-482`.
- **Rule**: the business rule as a sentence — `Withdrawals must not exceed
  the available balance`.
- **Scenario**: rule + which example this is, compressed — `Withdrawal
  exceeding the balance`, `Third failed login locks the account`. If two
  scenarios' names differ only by a number, the names aren't done. Never
  restate the steps in the name; name the point of the example.

## Tense, person, and voice

- **Given** in present/present-perfect state phrasing: "Alice **has** an
  open account", "the inventory **contains** 3 widgets". Not "Alice opens
  an account" — that's an event, and events that matter deserve their own
  scenario.
- **When** in present tense, active: "Alice withdraws £80".
- **Then** as an observable consequence: "£80 **is dispensed**",
  "she **is told** the withdrawal exceeds her balance". Passive voice is
  natural here. "Should" is debated; prefer the plain form ("is dispensed"
  over "should be dispensed") and follow the repo's convention if one
  exists.
- **Third person, named actors** ("Alice", "the account holder") over
  first-person "I" — third person forces you to say who the actor is,
  matters as soon as two actors interact, and keeps personas consistent.
  A repo already written in "I" is a convention to follow, not a war to
  start mid-file.

## Step reuse and automation cost

Every distinct step phrasing is a step definition someone implements and
maintains. Before inventing a phrasing, search existing `.feature` files
for a step that already says it and reuse it **verbatim** — "Alice has an
open account" and "Alice has got an open account" are two automations of
one fact. Parameterise where runners expect it (quoted strings and numbers
become capture groups: `she withdraws £80` matches `she withdraws £{int}`),
so steps vary by data, not by wording. Consistent personas (same names,
same roles, across files) compound this reuse.

## Anti-pattern catalogue

Each entry: the smell, why it hurts, the fix.

**Multiple When/Then cycles in one scenario.** A scenario asserting an
outcome, acting again, asserting again is a journey script: when it fails
you don't know which rule broke, and it can't be understood as an example
of anything. Split at each When into separate scenarios; the earlier steps
compress into the later scenario's Givens ("Given Alice has logged in").
Genuine end-to-end journeys may keep a few, tagged and kept rare.

**No When, or no Then.** Without a When nothing happens; without a Then
nothing is proven. A Given+Then scenario is acceptable only when the
"event" is genuinely just observation. A missing Then usually means the
author didn't know the expected outcome — which is the question to take
back to the business, not a scenario to ship.

**Conjunctive steps.** "When Alice logs in and withdraws £80 and checks
her balance" — three steps welded into one definition, unusable elsewhere.
One clause per step line; that's what `And` is for.

**Incidental detail.** A registration scenario specifying Alice's address,
phone, and marketing preferences when the rule under test is password
strength. Every irrelevant value invites the reader to wonder why it
matters. State only what changes the outcome (Essential); push default
data into step definitions.

**Hidden data coupling.** A Then asserting "£20 remains" when no Given
established the £100 balance — the outcome depends on data living in the
automation layer or, worse, a shared environment. Every value a Then
depends on must be derivable from the scenario's own text.

**Scenario chaining.** Scenario 2 assumes scenario 1 ran (the account
scenario 1 created, the login it performed). Breaks under parallel or
filtered runs. Each scenario builds its own world in Givens; if that feels
expensive, that's setup-automation feedback, not a reason to chain.

**Technical setup in the spec.** "Given the database is truncated",
"Given the mock payment service returns 200". The business can't read it
and it welds the spec to today's architecture. Move to hooks or express
the intent ("Given the payment provider is accepting payments").

**Outline abuse.** A Scenario Outline whose Examples mix accepted and
rejected rows under one generic Then ("Then the result is <result>"), or
an outline with one row, or columns that never vary. Split per outcome
(or use multiple named Examples blocks), inline single rows into a plain
scenario, delete constant columns.

**Wall of scenarios.** Twenty scenarios covering one rule's input space.
Gherkin documents behaviour by example; exhaustive coverage belongs in
unit tests. Keep the examples a business reader would want; if the team
needs the matrix, one outline with a curated table.

**Feature file as test suite dumping ground.** One file accumulating
login, search, and checkout scenarios because they share a tag or a
sprint. One capability per file; the filename should predict its contents.

## Review checklist

Walk this before delivering any feature file:

1. Feature has a description saying who needs it and why (story narrative
   or equivalent context).
2. Every scenario name states its point; no `Test 1`, no restated steps.
3. Exactly one When per scenario (journeys excepted, deliberately).
4. Givens are state, Whens are actions, Thens are outcomes observable by
   the actor — keyword intent never lies.
5. No UI mechanics (click/type/select/navigate/URL/field) outside a
   UI-spec feature.
6. Every value asserted in a Then traces to a Given, the When, or an
   Examples column.
7. Scenarios are order-independent; nothing assumes another scenario ran.
8. Background (if any) is short, Given-only, and needed by *every*
   scenario beneath it.
9. Outlines: >1 row, every column varies, accepted/rejected split apart.
10. Steps reuse existing phrasing where it exists; new phrasings are
    parameterised, business-worded, one clause each.
11. Tags are ones the team's filters/hooks actually use.
12. Read the file top to bottom as prose: a newcomer should learn the
    rules of this capability from it. If not, the file isn't done.
