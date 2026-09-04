---
name: gherkin-feature-authoring
description: >-
  Author, edit, and review Gherkin feature files (.feature) — BDD
  specifications in Given/When/Then for Cucumber, SpecFlow/Reqnroll, Behave,
  behat and similar tools. Use when the user wants feature files or BDD
  scenarios written or improved, wants a user story or acceptance criteria
  turned into scenarios, mentions Gherkin, Cucumber, Given/When/Then, scenario
  outlines, or .feature files, or asks to review scenarios for style or
  automation-readiness — even if they just say "write the acceptance tests
  for X as scenarios".
---

# Authoring Gherkin feature files

Gherkin is executable specification: each scenario is one concrete example
of a business rule, readable by the product owner and automatable by the
developer. Six rules carry most of the value. Apply them from this file;
open the references only in the cases listed at the end.

## The rules

1. **One `Rule:` per business rule, one scenario per example.** Read the
   acceptance criteria as a list of rules; give each its own `Rule:` block
   with the fewest examples that would catch a wrong implementation —
   normal case, boundary, rejection. Exhaustive matrices belong in unit
   tests.
2. **One behaviour per scenario.** Given = state, exactly one When = the
   event, Then = an outcome the actor can observe. A second When is a
   second scenario hiding in this one.
3. **Declarative, business language.** "Alice registers", never "clicks
   Submit" — UI mechanics live in step definitions, where they can change
   without rewriting the spec. Use real, consistent data ("Alice", "£80")
   and make every value a Then asserts derivable from the scenario's own
   text.
4. **Independent scenarios.** Each passes alone and in any order; if B
   needs what A did, fold it into B's Givens.
5. **Rewrites preserve every behaviour.** Each event the original
   exercised — a payment, a *view* of order history, a rejected checkout —
   keeps its own scenario with its own When, even when you could assert
   its outcome inside another scenario's Then. A Then cannot stand in for
   the event that reveals it, and folding or dropping one is silent
   requirements loss. Where the original states no expected outcome, don't
   invent one silently: write the most plausible outcome and flag it as a
   question for the business.
6. **Reuse step phrasing verbatim**, varying only values — every new
   wording is a new step definition to automate. Scenarios that differ
   only in data become one Scenario Outline.

## The shape

```gherkin
Feature: Account withdrawal
  As an account holder, I want to withdraw cash
  so that I can pay where cards are not accepted.

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

The Feature description says who needs this and why. `Background` is for
short, Given-only setup every scenario needs. Scenario names state the
point ("Withdrawal exceeding the balance"), never "Test 3".

## Naming the smells in a review

A review write-up can cite these directly, no reference needed:
**imperative UI script** (clicks, URLs, field names) · **journey scenario**
(several When/Then cycles) · **conjunctive step** ("… and … and …") ·
**scenario chaining** (depends on another scenario having run) · **missing
Then** (nothing proven) · **technical setup in the spec** (database
cleared, mocks) · **incidental detail / test-jargon data** · **meaningless
names** ("Test 1") and **no feature narrative** · **outline abuse** (one
row, constant columns, mixed accepted/rejected rows).

## After authoring

A finished feature file is a specification waiting to become a test gate,
not just documentation. When an implementation exists or is starting, hand
over to the `cucumber-js-automation` skill (where available, for JS/TS
projects) to bind the scenarios to code and wire the suite into CI.

## When to open the references

- [references/style.md](references/style.md) — only for the worked
  before/after rewrites of each smell or the full pre-delivery checklist;
  the names above are enough for a review.
- [references/syntax.md](references/syntax.md) — for a construct you don't
  use daily: data tables, doc strings, tags, multiple Examples blocks,
  `# language:`, escaping.
- [assets/template.feature](assets/template.feature) — a longer worked
  example (outline, data table, several rules) if the shape above isn't
  enough.
- Spec: https://cucumber.io/docs/gherkin/reference
