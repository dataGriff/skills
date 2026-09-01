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

Write Gherkin as **executable specification**, not a test script that
happens to use Given/When/Then. A `.feature` file describes one capability
in business language; each scenario is one concrete example of a rule the
business cares about. If a scenario would not help a product owner and a
developer agree on behaviour, rewrite it until it would.

Start from [assets/template.feature](assets/template.feature) — copy and
adapt rather than writing from a blank page. Load
[references/style.md](references/style.md) before writing more than a
trivial scenario or reviewing existing files — it holds the style rules,
anti-pattern catalogue, and the pre-delivery review checklist. Open
[references/syntax.md](references/syntax.md) only when you need construct
detail (Rule, Background, outlines, tables, doc strings, tags, `#
language:`, escaping).

## Workflow

1. **Get the rules before the syntax.** From the story or acceptance
   criteria, list the business rules and, per rule, the concrete examples
   that pin it down: the normal case, the boundary, the rejection. Each
   example becomes one scenario; a vague criterion becomes a question for
   the user, not an invented behaviour.
2. **Structure the file.** One `Feature` per file, named for the capability,
   with a narrative description (who needs it and why). One `Rule:` per
   business rule when there are several. `Background` only for short,
   Given-only setup every scenario needs.
3. **Write each scenario around exactly one behaviour.** `Given` the state
   that matters, one `When` — the event under test — `Then` the outcome
   observable by the actor. Name it after rule + example ("Withdrawal
   exceeding the balance"), never "Test 3".
4. **Stay declarative.** Say what the actor does ("Alice registers"), never
   how the UI does it ("clicks Submit") — UI mechanics live in step
   definitions. Use real, consistent data ("Alice", "£80"), and make every
   value a `Then` asserts derivable from the scenario's own text.
5. **Collapse same-shape scenarios into a Scenario Outline** — two scenarios
   differing only in values are one outline. Keep `Examples` columns to what
   varies; split accepted from rejected rows into separate scenarios or
   named Examples blocks rather than one generic "the result is <result>".
6. **Tag for selection, not decoration**, then walk the review checklist at
   the end of [references/style.md](references/style.md) before delivering.

## Authoring judgment

- **Examples, not permutations.** Cover each rule with the fewest examples
  that would catch a wrong implementation; exhaustive input matrices belong
  in unit tests.
- **Keyword intent never lies.** Given = state (past/present-perfect),
  When = the one event, Then = observable consequence — runners don't
  check this, readers depend on it.
- **Independence is non-negotiable.** Every scenario passes alone and in
  any order; if B needs what A did, fold it into B's Givens.
- **Reuse step phrasing verbatim.** Every new wording is a new step
  definition to automate — match the repo's existing vocabulary and
  personas before inventing your own.

## References

- [references/style.md](references/style.md) — BRIEF, declarative style
  with rewrites, naming/tense/person, anti-pattern catalogue, review
  checklist.
- [references/syntax.md](references/syntax.md) — every keyword and
  construct, with escaping rules.
- [assets/template.feature](assets/template.feature) — lint-clean example
  demonstrating the constructs in good style.
- Authoritative syntax reference: https://cucumber.io/docs/gherkin/reference
