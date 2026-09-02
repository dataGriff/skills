# Setup, configuration, and runners

Project wiring for a Cucumber.js suite: config files, module systems,
TypeScript, reporting, CI, and when to reach for a different Gherkin
runner. Binding syntax lives in [api.md](api.md).

## Contents

- [Install](#install)
- [Configuration files and profiles](#configuration-files-and-profiles)
- [Key options](#key-options)
- [ESM vs CommonJS](#esm-vs-commonjs)
- [TypeScript](#typescript)
- [Formatters and reports](#formatters-and-reports)
- [Retries](#retries)
- [CI wiring](#ci-wiring)
- [Other Gherkin runners](#other-gherkin-runners)

## Install

```bash
npm install --save-dev @cucumber/cucumber
```

Requires an actively supported Node.js. The runner is `npx cucumber-js`;
add `"test:bdd": "cucumber-js"` to `package.json` scripts so the suite is
discoverable. Don't confuse the package with the long-deprecated
`cucumber` npm name.

## Configuration files and profiles

Cucumber.js picks up `cucumber.js`, `cucumber.cjs`, `cucumber.mjs`,
`cucumber.json`, or `cucumber.yaml` from the project root. Each top-level
key is a profile; `default` applies unless `-p <name>` selects another —
profiles are plain objects, so build them by spreading shared bits:

```javascript
// cucumber.js
const common = {
  format: ['progress-bar'],
  worldParameters: { baseUrl: 'http://localhost:3000' },
};

module.exports = {
  default: { ...common },
  ci: {
    ...common,
    format: ['progress', 'html:reports/cucumber.html', 'junit:reports/junit.xml'],
    parallel: 2,
    retry: 1,
    retryTagFilter: '@flaky',
  },
};
```

```bash
npx cucumber-js -p ci
```

CLI flags override the profile; use the file for anything repeatable.

## Key options

| Option            | CLI                  | Meaning                                            |
| ----------------- | -------------------- | -------------------------------------------------- |
| `paths`           | positional args      | feature files/globs (default `features/**/*.feature`) |
| `require`         | `--require`          | CommonJS support-code globs                        |
| `import`          | `--import`           | ESM support-code globs                             |
| `requireModule`   | `--require-module`   | transpilers to register first (e.g. `ts-node/register`) |
| `format`          | `--format`           | formatter, optionally `name:path`                  |
| `parallel`        | `--parallel`         | worker count                                       |
| `tags`            | `--tags`             | tag expression filter                              |
| `retry`           | `--retry`            | re-run attempts for failing scenarios              |
| `retryTagFilter`  | `--retry-tag-filter` | limit retry to matching tags                       |
| `worldParameters` | `--world-parameters` | JSON object exposed as `this.parameters`           |
| `dryRun`          | `--dry-run`          | bind every step, execute nothing                   |
| `failFast`        | `--fail-fast`        | stop on first failure                              |
| `strict`          | `--strict`           | pending steps fail the run (default true)          |

When features or steps live outside the default layout, set `paths` plus
`require`/`import` explicitly — the defaults only cover `features/`.

## ESM vs CommonJS

Cucumber.js supports both; the support-code loading option is what
differs.

- **CommonJS** (no `"type": "module"`): `require()` in support files;
  config option `require` (defaults cover `features/**/*.js`).
- **ESM** (`"type": "module"` or `.mjs` files): `import` statements in
  support files, and the config **must** list them under `import` —
  `require` cannot load ES modules:

```javascript
// cucumber.mjs
export default {
  default: { import: ['features/**/*.js'] },
};
```

Don't mix: pick the module system the project already uses and load all
support code through the matching option.

## TypeScript

CommonJS projects — register ts-node and point `require` at the TS
sources:

```javascript
// cucumber.js
module.exports = {
  default: {
    requireModule: ['ts-node/register'],
    require: ['features/**/*.ts'],
  },
};
```

ESM projects — run through a TS loader and use `import` globs:

```bash
NODE_OPTIONS='--import tsx' npx cucumber-js
```

```javascript
// cucumber.mjs
export default { default: { import: ['features/**/*.ts'] } };
```

Type the World once and steps get typed `this`:

```typescript
import { Given, World } from '@cucumber/cucumber';

class AppWorld extends World { bank!: Bank; }
Given('…', async function (this: AppWorld, amount: number) { … });
```

## Formatters and reports

Built-in formatters: `progress` (default), `progress-bar`, `summary`,
`pretty`, `html`, `json`, `junit`, `message`, `rerun`, `snippets`,
`usage`. Several can run at once; `name:path` writes to a file:

```bash
npx cucumber-js --format html:reports/cucumber.html --format junit:reports/junit.xml
```

- `html` — single self-contained file with attachments; the one to hand
  to humans.
- `junit` — what CI systems ingest for test-result UIs.
- `rerun` — writes failed scenario locations to a file;
  `npx cucumber-js @rerun.txt` re-runs just those.
- `usage` — step-definition timing and reuse; spots dead and slow steps.

## Retries

`retry` re-runs failing scenarios and reports the last attempt. It is a
mitigation, not a fix: pair it with `retryTagFilter: '@flaky'` so only
scenarios explicitly marked flaky get the indulgence, and treat every
`@flaky` tag as a bug to remove. A blanket retry hides real regressions
behind green runs.

## CI wiring

The exit code is the contract: non-zero on failing, undefined, ambiguous,
or (under `strict`, the default) pending steps.

```yaml
# e.g. GitHub Actions
- run: npm ci
- run: npx cucumber-js -p ci
- uses: actions/upload-artifact@v4
  if: failure()
  with: { name: cucumber-report, path: reports/ }
```

Boot any app under test before the run (health-checked, not `sleep`) and
pass its address through `worldParameters`, keeping environment plumbing
out of step definitions.

## Other Gherkin runners

`@cucumber/cucumber` is the reference implementation and the default
choice. Reach elsewhere when the project's tooling dictates:

- **playwright-bdd** — generates Playwright tests from features; choose
  it when the suite is browser E2E already standardised on Playwright
  (trace viewer, fixtures, sharding).
- **jest-cucumber / vitest-cucumber** — features drive tests inside an
  existing Jest/Vitest setup (one spec file per feature,
  `defineFeature`/`loadFeature`); choose when the team wants BDD inside
  its unit-test runner rather than a second CLI.
- **@badeball/cypress-cucumber-preprocessor** — the maintained
  preprocessor when the E2E stack is Cypress.

All of them execute the same Gherkin, so features stay portable; only the
glue code differs.
