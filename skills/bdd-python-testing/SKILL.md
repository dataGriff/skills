---
name: bdd-python-testing
description: >-
  Implement BDD tests in Python from Gherkin syntax — wire Given/When/Then
  scenarios in .feature files to executable step definitions with pytest-bdd
  or behave. Use when the user wants BDD-style testing in Python, wants
  feature files automated, run, or hooked up to code, asks for step
  definitions, mentions pytest-bdd or behave, or has Gherkin scenarios that
  need a test harness — even if they just say "make these scenarios
  executable" or "add BDD tests to my Python project". For writing or
  reviewing the .feature files themselves, use gherkin-feature-authoring.
---

# BDD testing in Python

A BDD suite has three layers, and keeping them separate is what makes it
maintainable: the **feature file** (business-readable spec), the **step
definitions** (glue that binds each Gherkin phrase to code), and the
**support code** (fixtures, drivers, domain helpers that do the actual
work). Steps stay thin; mechanics live underneath so the spec never changes
when the implementation does.

If the feature files don't exist yet, write them first — with the
`gherkin-feature-authoring` skill if available — and get the behaviour
right in Gherkin before writing any Python.

## Choose the tool

- **pytest-bdd** (default): use when the project already uses pytest or has
  any other pytest tests. Steps are plain pytest — fixtures, markers,
  plugins (coverage, xdist, CI reporting) all work unchanged, and BDD and
  non-BDD tests run in one suite.
- **behave**: use when the user asks for it, the project already has a
  `features/` tree with an `environment.py`, or they want the
  Cucumber-style standalone runner (`behave` command, `context` object).

Don't mix both in one project. Match whichever is already installed.

## Workflow

1. **Read the feature files first.** List every distinct step phrasing —
   each one needs exactly one definition. Steps that differ only in values
   ("Alice withdraws £80" / "Alice withdraws £120") are one parameterised
   definition, not two.
2. **Set up the layout** (see the tool sections below) so the runner finds
   features and steps.
3. **Write the step definitions**, thinnest possible: Given arranges state,
   the single When performs the action and captures its outcome (including
   an expected error — don't let it escape), Then only asserts. No
   assertions in Given/When, no actions in Then.
4. **Push real work down** into fixtures and helper/driver functions the
   steps call. A step body over ~5 lines is usually hiding support code.
5. **Run the suite and let the tool report unbound steps** — both tools
   name missing steps and print definition snippets; don't hand-check
   bindings.

## pytest-bdd shape

```
tests/
├── features/withdrawal.feature
├── conftest.py            # shared fixtures and cross-file steps
└── test_withdrawal.py     # binds the feature, holds its steps
```

```python
# test_withdrawal.py
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("features/withdrawal.feature")  # binds every scenario in the file

@given(parsers.parse("Alice has an open account with a balance of £{balance:d}"),
       target_fixture="account")
def account(balance):
    return Account(owner="Alice", balance=balance)

@when(parsers.parse("Alice withdraws £{amount:d}"), target_fixture="dispensed")
def withdraw(account, amount):
    return account.withdraw(amount)

@then(parsers.parse("£{amount:d} is dispensed"))
def check_dispensed(dispensed, amount):
    assert dispensed == amount

@then(parsers.parse("Alice's balance is £{remaining:d}"))
def check_balance(account, remaining):
    assert account.balance == remaining
```

State flows between steps as fixtures: a Given/When returns a value via
`target_fixture`, later steps take it as an argument. Never pass state
through globals or class attributes. Run with plain `pytest`; Gherkin tags
become pytest markers (`@smoke` → `-m smoke`, register markers to silence
warnings).

## behave shape

```
features/
├── withdrawal.feature
├── environment.py         # hooks: before_all, before_scenario, …
└── steps/withdrawal_steps.py
```

```python
# steps/withdrawal_steps.py
from behave import given, when, then

@given("Alice has an open account with a balance of £{balance:d}")
def step_account(context, balance):
    context.account = Account(owner="Alice", balance=balance)

@when("Alice withdraws £{amount:d}")
def step_withdraw(context, amount):
    context.dispensed = context.account.withdraw(amount)

@then("£{amount:d} is dispensed")
def step_check_dispensed(context, amount):
    assert context.dispensed == amount, (
        f"expected £{amount}, got £{context.dispensed}")
```

State lives on `context`, which is reset per scenario. Setup/teardown goes
in `environment.py` hooks, not in steps. Run with `behave`; filter with
`behave --tags=@smoke`. behave's plain `assert` gives poor failure output,
so always add a message (or use a matcher library).

## Rules that keep the suite honest

- **The feature file is the contract.** Don't reword Gherkin to make
  binding easier; the glue adapts to the spec. If a phrasing is genuinely
  unautomatable, flag it to the user rather than silently rewriting it.
- **One definition per phrasing, parameterised by values.** Two near-identical
  step functions mean the parser pattern is wrong.
- **Scenarios are independent.** Fresh state per scenario (fixtures /
  `context` + hooks); a scenario must pass alone and in any order. Never
  count on scenario A having run before B.
- **A When that can fail captures, never raises.** Store the outcome or
  exception so a Then can assert on it; a rejection scenario that crashes
  in the When step is a broken test, not a passing spec.
- **Scenario Outlines need no special steps** — each Examples row runs as
  its own scenario and the parameterised definitions match the substituted
  values.

## When to open the references

- [references/pytest-bdd.md](references/pytest-bdd.md) — only for
  pytest-bdd mechanics beyond the shape above: parser flavours and custom
  types, data tables and docstrings, `@scenario` vs `scenarios`, sharing
  steps in conftest, outlines, tags/hooks, config (`bdd_features_base_dir`),
  generating missing steps.
- [references/behave.md](references/behave.md) — only for behave mechanics
  beyond the shape above: step matchers (`re`, `cfparse`) and custom types,
  `context.table`/`context.text`, environment hooks and behave fixtures,
  tags, runner options and CI output, step catalogs.
