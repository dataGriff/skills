---
name: cucumber-js-automation
description: >-
  Implement Gherkin feature files as executable BDD tests in JavaScript or
  TypeScript with Cucumber.js (@cucumber/cucumber) — project setup, step
  definitions, World state, hooks, data tables, and run configuration. Use
  when the user wants Given/When/Then scenarios automated in a JS/TS/Node
  project, asks for step definitions or glue code for a .feature file,
  mentions cucumber-js, BDD or acceptance testing in JavaScript, has
  undefined or pending steps to implement, or wants Gherkin scenarios wired
  up to run against their code — even if they just say "make these
  scenarios executable" or "add BDD tests".
---

# Cucumber.js automation

Turn Gherkin feature files into a running BDD suite with
[Cucumber.js](https://github.com/cucumber/cucumber-js). This skill covers
the automation layer: step definitions, shared state, hooks, and the test
run. Writing or improving the `.feature` files themselves is a separate
concern (the `gherkin-feature-authoring` skill, where available) — keep
scenarios declarative and put all mechanics below the steps, here.

## Project shape

```
features/
├── account-withdrawal.feature      the Gherkin specs
├── step_definitions/
│   └── account.steps.js            Given/When/Then bindings
└── support/
    ├── world.js                    per-scenario state (World)
    └── hooks.js                    Before/After setup and teardown
src/                                the code under test
```

```bash
npm install --save-dev @cucumber/cucumber
npx cucumber-js            # runs features/**/*.feature with this layout
```

Cucumber.js finds features and support code in these default locations —
keep the layout unless the project already has its own. It exits non-zero
on failing, undefined, ambiguous, or pending steps, so a green run means
every step is both bound and passing.

## The rules

1. **Let cucumber-js tell you which steps to write.** Run
   `npx cucumber-js` against the feature first: every undefined step is
   reported with a ready-made snippet (correct expression and arity).
   Implement from those snippets instead of guessing phrasings — a
   mistyped expression silently leaves the real step undefined.
2. **One definition per phrasing, matched by Cucumber expressions.**
   `{int}`, `{float}`, `{string}`, `{word}` capture values and convert
   types; prefer them over regex, which is harder to read and to reuse.
   Scenarios that reuse a phrasing with different values must hit the
   same definition — if a new step differs only in wording, align the
   feature wording rather than adding a near-duplicate definition.
3. **Scenario state lives on the World (`this`), never module scope.**
   Each scenario gets a fresh World, so scenarios stay independent and
   can run in parallel; module-level variables that steps mutate leak
   state between scenarios and break under `--parallel`. The one
   legitimate module-scope resident is a per-run resource created in
   `BeforeAll`/`AfterAll` (which have no World) — a server handle, a
   connection pool — and steps still only read it. Use `function () {}`
   for steps and hooks —
   an arrow function cannot bind `this`, and every value it needed
   becomes invisible to the World.
4. **Steps are thin; mechanics live below them.** A step definition maps
   one business phrase onto a driver/service layer (or the module under
   test) in a few lines. HTTP calls, browser automation, and builders
   belong in `support/` or a driver module, where they can change without
   touching the bindings.
5. **Given arranges, When acts and captures, Then asserts.** Assertions
   (use `node:assert/strict` or the project's assertion library) belong
   in Then steps only. A When that exercises a failure path catches the
   error for Then to inspect:
   `this.error = await this.bank.withdraw('Alice', 120).catch(e => e);`
   — never let an expected rejection fail the step itself.
6. **Setup and teardown go in hooks, not steps.** `Before`/`After` run
   per scenario; `BeforeAll`/`AfterAll` per run; tag hooks
   (`Before({ tags: '@db' }, …)`) to scope expensive resources to the
   scenarios that need them. `After` hooks run even when the scenario
   fails — put cleanup there, never in a Then.
7. **Everything is async.** `await` every promise and mark the function
   `async`; a step that returns early passes vacuously and asserts
   nothing. Don't use the legacy callback style.

## Worked example

```gherkin
Feature: Account withdrawal

  Scenario: Withdrawal within the balance
    Given Alice has an open account with a balance of £100
    When Alice withdraws £80
    Then Alice's balance is £20
```

```javascript
// features/step_definitions/account.steps.js
const assert = require('node:assert/strict');
const { Given, When, Then } = require('@cucumber/cucumber');

Given('{word} has an open account with a balance of £{int}',
  function (name, balance) {
    this.bank.openAccount(name, balance);
  });

When('{word} withdraws £{int}', async function (name, amount) {
  await this.bank.withdraw(name, amount);
});

Then("{word}'s balance is £{int}", function (name, expected) {
  assert.equal(this.bank.balanceOf(name), expected);
});
```

```javascript
// features/support/world.js
const { setWorldConstructor, World } = require('@cucumber/cucumber');
const { Bank } = require('../../src/bank');

class BankWorld extends World {
  constructor(options) {
    super(options);          // keeps this.attach / this.log / this.parameters
    this.bank = new Bank();  // fresh per scenario
  }
}
setWorldConstructor(BankWorld);
```

In an ESM project (`"type": "module"`) use `import` syntax and run with
the `import` configuration option instead of `require` — details in
[references/setup.md](references/setup.md).

## Running the suite

```bash
npx cucumber-js                                  # whole suite
npx cucumber-js features/withdrawal.feature:12   # one scenario, by line
npx cucumber-js --tags '@wip and not @slow'      # tag expression
npx cucumber-js --dry-run                        # check every step binds, run nothing
npx cucumber-js --parallel 4                     # workers (needs rule 3)
```

Repeatable options belong in a `cucumber.js`/`cucumber.mjs` config file
with profiles (`npx cucumber-js -p ci`), not in a growing shell command.

## When to open the references

- [references/api.md](references/api.md) — when a binding needs more than
  the basics above: custom parameter types, data tables and doc strings,
  the full hook set, timeouts, tags, attachments, Scenario Outline
  interplay, parallel-safety details.
- [references/setup.md](references/setup.md) — when configuring rather
  than writing steps: config files and profiles, ESM vs CommonJS,
  TypeScript, formatters and CI reports, retries, and when a different
  runner (jest-cucumber, playwright-bdd, …) fits better than cucumber-js.
