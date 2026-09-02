# Cucumber.js binding API

Everything a step definition, hook, or World might need beyond the basics
in SKILL.md. Examples use CommonJS; swap `require` for `import` in ESM
projects (see [setup.md](setup.md)).

## Contents

- [Cucumber expressions](#cucumber-expressions)
- [Custom parameter types](#custom-parameter-types)
- [Data tables](#data-tables)
- [Doc strings](#doc-strings)
- [Scenario Outlines](#scenario-outlines)
- [Hooks](#hooks)
- [World](#world)
- [Timeouts](#timeouts)
- [Tags](#tags)
- [Attachments and logging](#attachments-and-logging)
- [Parallel safety](#parallel-safety)

## Cucumber expressions

| Syntax        | Matches                                | Passed to the step as |
| ------------- | -------------------------------------- | --------------------- |
| `{int}`       | `42`, `-3`                             | `number`              |
| `{float}`     | `3.14`, `-0.5`                         | `number`              |
| `{string}`    | `"hello"` or `'hello'` (quotes eaten)  | `string`              |
| `{word}`      | one non-whitespace word (`Alice`)      | `string`              |
| `{}`          | anything, non-greedy                   | `string`              |
| `text/texts`  | alternative text: matches either       | — (not captured)      |
| `mayb(es)`    | optional text: `mayb` or `maybes`      | — (not captured)      |
| `\{` `\(`     | literal brace / parenthesis            | —                     |

Alternation and optionals keep one definition serving several phrasings:

```javascript
Then('the withdrawal/deposit is rejected', function () { … });
Given('Alice has {int} item(s) in her basket', function (count) { … });
```

A plain `RegExp` first argument also works (`When(/^Alice pays £(\d+)$/, …)`)
— reserve it for matches Cucumber expressions genuinely cannot express.

## Custom parameter types

Convert domain values once, at the boundary, instead of in every step:

```javascript
const { defineParameterType } = require('@cucumber/cucumber');

defineParameterType({
  name: 'money',                 // used as {money} in expressions
  regexp: /£(\d+(?:\.\d{2})?)/,
  transformer: (amount) => Math.round(parseFloat(amount) * 100), // pence
});

When('{word} withdraws {money}', function (name, pence) { … });
```

Define these in `features/support/` so every step file sees them. The
`transformer` runs with `this` bound to the World.

## Data tables

A table under a step arrives as the last argument, a `DataTable`:

```gherkin
Given the following accounts:
  | owner | balance |
  | Alice | 100     |
  | Bob   | 40      |
```

```javascript
Given('the following accounts:', function (table) {
  for (const row of table.hashes()) {          // [{ owner: 'Alice', balance: '100' }, …]
    this.bank.openAccount(row.owner, Number(row.balance));
  }
});
```

| Method        | Shape returned                                          |
| ------------- | ------------------------------------------------------- |
| `hashes()`    | array of objects keyed by the header row                |
| `rows()`      | array of string arrays, header row dropped              |
| `raw()`       | array of string arrays, header row included             |
| `rowsHash()`  | object from two-column tables: first column → second    |
| `transpose()` | new DataTable with rows and columns swapped             |

All cell values are strings — convert numbers explicitly.

## Doc strings

A triple-quoted block under a step arrives as a trailing string argument
(after any expression captures). The content type annotation
(` ```json `) is documentation only; parse it yourself:

```javascript
When('the client POSTs the payload:', async function (body) {
  this.response = await this.api.post('/orders', JSON.parse(body));
});
```

## Scenario Outlines

Each `Examples:` row expands into its own scenario before matching, so
outlines need nothing special in the bindings: `<column>` placeholders
are substituted into the step text first, and the expanded text must
match a definition. Write the expression against the substituted values
(`When Alice withdraws £{int}` matches `When Alice withdraws £<amount>`
for every numeric row).

## Hooks

```javascript
const { Before, After, BeforeAll, AfterAll,
        BeforeStep, AfterStep, setDefaultTimeout } = require('@cucumber/cucumber');

BeforeAll(async function () { … });   // once per run — NO World; share via module scope
Before(async function () { … });      // per scenario, fresh World bound to `this`
Before({ tags: '@db' }, async function () { … });  // only scenarios tagged @db
Before({ name: 'seed users' }, async function () { … });  // named in output
After(async function ({ result, pickle }) {
  // runs even when the scenario failed — cleanup goes here
  if (result.status === 'FAILED') { … }  // e.g. attach a screenshot
});
BeforeStep(async function () { … });  // rarely needed; keep them cheap
AfterAll(async function () { … });    // once per run
```

Ordering: `Before` hooks run in definition order, `After` hooks in
reverse. `BeforeAll`/`AfterAll` run per worker under `--parallel`.

## World

`setWorldConstructor` replaces the per-scenario state object. Extend the
built-in `World` to keep the framework goodies:

```javascript
const { setWorldConstructor, World } = require('@cucumber/cucumber');

class AppWorld extends World {
  constructor(options) {
    super(options);   // wires this.attach, this.log, this.parameters
    this.driver = null;
  }
  async openBrowser() { … }   // helpers steps can call as this.openBrowser()
}
setWorldConstructor(AppWorld);
```

`this.parameters` carries `worldParameters` from the config file / CLI
(`--world-parameters '{"baseUrl":"http://localhost:3000"}'`) — the right
channel for environment differences, instead of `process.env` reads
scattered through steps.

## Timeouts

Default: 5000 ms per step or hook.

```javascript
const { setDefaultTimeout, Before } = require('@cucumber/cucumber');
setDefaultTimeout(15 * 1000);                       // whole suite
Before({ timeout: 60 * 1000 }, async function () { … });  // one hook
When('a slow import runs', { timeout: 120 * 1000 }, async function () { … });
setDefaultTimeout(-1);                              // disable (debugging only)
```

A timeout failure usually means a missing `await` or a hanging resource —
raise the limit only when the operation is legitimately slow.

## Tags

Tags on a Feature/Rule/Scenario/Examples select work at run time:

```bash
npx cucumber-js --tags '@smoke'
npx cucumber-js --tags '@fast and not @flaky'
npx cucumber-js --tags '(@web or @api) and not @wip'
```

The same expressions scope hooks (`Before({ tags: '@db' }, …)`). Use tags
for orthogonal concerns (speed, resource needs, work-in-progress) — not
to encode suites that directory structure already expresses.

## Attachments and logging

Inside steps and `Before`/`After` hooks (never `BeforeAll`/`AfterAll`):

```javascript
this.log('created order ' + order.id);                        // text
this.attach(JSON.stringify(response.body), 'application/json');
this.attach(await page.screenshot(), 'image/png');            // Buffer
```

Attachments land in reports (html/json formatters) next to the step that
made them — attach on failure in an `After` hook for debuggable CI runs.

## Parallel safety

`--parallel N` runs N worker processes; each scenario still gets a fresh
World. What breaks it:

- module-scope mutable state in step files (rule 3 in SKILL.md);
- shared external resources — give each worker its own database/schema or
  port, keyed off `process.env.CUCUMBER_WORKER_ID`;
- order-dependent scenarios — they were already wrong, parallelism just
  exposes them.

Full options reference: https://github.com/cucumber/cucumber-js/blob/main/docs/support_files/api_reference.md
