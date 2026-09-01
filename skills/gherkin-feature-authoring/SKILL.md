---
name: gherkin-feature-authoring
description: >-
  Author, edit, and review Gherkin feature files (.feature) — executable BDD
  specifications in Given/When/Then form for Cucumber, SpecFlow/Reqnroll,
  Behave, behat, and similar tools. Covers feature/scenario structure, Rule
  and Background, Scenario Outlines with Examples, data tables, doc strings,
  tags, and declarative BRIEF-style writing that survives automation. Use
  when the user wants to write or improve feature files or BDD scenarios,
  turn a user story or acceptance criteria into scenarios, mentions Gherkin,
  Cucumber, Given/When/Then, scenario outlines, or .feature files, or asks
  to review scenarios for style, duplication, or automation-readiness — even
  if they just say "write the acceptance tests for X as scenarios".
---

# Authoring Gherkin feature files

Write Gherkin as **executable specification**, not as a test script that
happens to use Given/When/Then. Each `.feature` file describes one capability
of the system in business language; each scenario is a single concrete
example of a rule the business cares about. If a scenario would not help a
product owner and a developer agree on behaviour, rewrite it until it would.

Start from [assets/template.feature](assets/template.feature) — copy it and
adapt rather than writing from a blank page.

## The shape of a feature file

```gherkin
Feature: Account withdrawal
  As an account holder, I want to withdraw cash
  so that I can pay where cards are not accepted.

  Free text under Feature: (until the first keyword) is the place for
  context, scope, and links — use it; a bare Feature line wastes the reader.

  Background:
    Given Alice has an open account with a balance of £100

  Rule: Withdrawals must not exceed the available balance

    Scenario: Withdrawal within the balance
      When Alice withdraws £80
      Then £80 is dispensed
      And Alice's balance is £20

    Scenario: Withdrawal exceeding the balance
      When Alice attempts to withdraw £120
      Then nothing is dispensed
      And she is told the withdrawal exceeds her balance
```

One `Feature` per file, named after the capability (not a screen, sprint, or
ticket). `Rule` groups the examples that illustrate one business rule —
use it when a feature has several rules; skip it when it has one.

## Workflow

1. **Get the rules before the syntax.** From the story, acceptance criteria,
   or conversation, list the business rules and, for each rule, the concrete
   examples that pin it down: the normal case, the boundary, the rejection.
   Each example becomes one scenario; each vague criterion becomes a
   question for the user, not an invented behaviour.
2. **Structure the file.** Feature name + narrative description, one `Rule`
   per business rule, shared setup in `Background` only if every scenario
   needs it and it fits in a few lines readers must keep in mind.
3. **Write each scenario declaratively** around exactly one behaviour:
   `Given` the state that matters, one `When` — the event under test — and
   `Then` the observable outcome. Name the scenario after the rule +
   example (`Scenario: Withdrawal exceeding the balance`), never
   `Scenario: Test 3`. Say *what* the actor does ("Alice registers"), never
   *how* the UI does it ("clicks the Submit button") — UI detail belongs in
   step definitions, where it can change without rewriting the spec. See
   [references/style.md](references/style.md) for the full style rules and
   the anti-pattern catalogue.
4. **Collapse repetition into a Scenario Outline** only when the same
   behaviour varies by data; keep the `Examples` table narrow (columns the
   rule actually varies on) and split tables per rule rather than mixing
   valid and invalid rows under one outline. Data tables and doc strings
   carry structured arguments inside a step. Syntax details:
   [references/syntax.md](references/syntax.md).
5. **Tag for selection, not decoration** — `@smoke`, `@wip`, a ticket id if
   the team runs on them. Tags on `Feature` are inherited by its scenarios.
6. **Review before delivering.** Walk the checklist at the end of
   [references/style.md](references/style.md): one When per scenario,
   no UI mechanics, no scenario depending on another having run, present
   tense/third person, every Then observable by the actor.

## Authoring judgment

- **Scenarios are examples, not permutations.** Cover each rule with the
  fewest examples that would catch a wrong implementation — typically one
  passing, one failing, one boundary. Exhaustive input matrices belong in
  unit tests, not Gherkin.
- **Given = past, When = present, Then = outcome.** Setup that reads like an
  action ("Given Alice logs in") hides an event in the state; outcomes that
  read like internals ("Then the row is inserted") are untestable by the
  business. State, event, observable consequence.
- **Independence is non-negotiable.** Any scenario must pass when run alone
  or in any order. If scenario B needs what scenario A did, fold that into
  B's `Given`.
- **Prefer real, consistent example data.** "Alice"/"Bob" with concrete
  amounts beat "user1" and `<value>` placeholders in plain scenarios;
  consistent personas across a repo let readers carry context between files.
- **A feature file is documentation with an audience.** When editing an
  existing repo, match its established phrasing and step vocabulary — reusing
  a step verbatim is worth more than a marginally nicer sentence, because
  every new phrasing is a new step definition to automate.

## References

- [references/syntax.md](references/syntax.md) — every keyword and
  construct: Feature, Rule, Background, Scenario/Example, steps and
  And/But/*, Scenario Outline + Examples, data tables, doc strings, tags,
  comments, `# language:` headers, and escaping.
- [references/style.md](references/style.md) — declarative style and the
  BRIEF principles, naming, tense and person, the anti-pattern catalogue
  (with rewrites), and the pre-delivery review checklist.
- [assets/template.feature](assets/template.feature) — a complete example
  file demonstrating the constructs in good style; copy and adapt.
- Authoritative syntax reference: https://cucumber.io/docs/gherkin/reference —
  consult for anything not covered here.
