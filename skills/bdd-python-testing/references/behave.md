# behave mechanics

Details beyond the core shape in SKILL.md.

## Contents

- [Layout rules](#layout-rules)
- [Step matchers and custom types](#step-matchers-and-custom-types)
- [The context object](#the-context-object)
- [Tables and docstrings](#tables-and-docstrings)
- [Environment hooks and fixtures](#environment-hooks-and-fixtures)
- [Tags](#tags)
- [Running and CI output](#running-and-ci-output)
- [Step catalog and undefined steps](#step-catalog-and-undefined-steps)

## Layout rules

behave is convention-bound: features live in `features/` (or the directory
passed on the command line), step modules in `features/steps/`, hooks in
`features/environment.py`. Every `steps/*.py` module is loaded for every
feature — step definitions are global, so a phrasing may be defined only
once across the whole tree. Organise step modules by domain area, not by
feature file, to keep that global namespace coherent.

## Step matchers and custom types

The default matcher is `parse` (format-string style, `{amount:d}`
converts). Switch per-module with:

```python
from behave import use_step_matcher, register_type
use_step_matcher("re")       # or "parse" (default), "cfparse"
```

`use_step_matcher` applies to the definitions that follow it in that
module, so a module can mix flavours — better not to. Custom conversions
are registered once, then usable in any `parse`/`cfparse` pattern:

```python
import parse

@parse.with_pattern(r"£\d+")
def parse_money(text):
    return int(text.lstrip("£"))

register_type(Money=parse_money)

@when("Alice withdraws {amount:Money}")
def step_withdraw(context, amount): ...
```

## The context object

`context` is layered: attributes set in `before_all` live for the run,
those set in `before_feature` for the feature, those set in steps for the
scenario — each layer is popped automatically, so scenario state cannot
leak. Conventions:

- Steps communicate only via `context` attributes; pick stable names
  (`context.response`, `context.error`) and use them consistently.
- Capture expected failures: `context.error = None` in the Given,
  try/except in the When, assert on `context.error` in the Then.
- `context.config` exposes the parsed config and `-D key=value` userdata
  (`context.config.userdata["base_url"]`) — the channel for
  environment-specific settings, not os.environ reads inside steps.

## Tables and docstrings

A step's table arrives as `context.table` (iterable of `Row`, keyed by
heading), a docstring as `context.text`:

```python
@given("the following accounts")
def step_accounts(context):
    context.accounts = [
        Account(owner=row["owner"], balance=int(row["balance"]))
        for row in context.table
    ]
```

`context.table` is `None` when the step has no table — only steps whose
Gherkin actually carries a table should touch it. Note the step text keeps
any trailing colon: `Given the following accounts:` binds to
`@given("the following accounts:")` — without the colon the step is
undefined.

## Environment hooks and fixtures

`environment.py` may define: `before_all/after_all`,
`before_feature/after_feature`, `before_scenario/after_scenario`,
`before_step/after_step`, `before_tag/after_tag`. Hooks own lifecycle work
(start the app, open/close browsers, transactions); steps own behaviour.

For per-tag setup with guaranteed cleanup, use behave fixtures:

```python
# environment.py
from behave import use_fixture
from behave.fixture import fixture

@fixture
def running_server(context):
    context.server = start_server()
    yield context.server
    context.server.stop()          # runs even when the scenario fails

def before_tag(context, tag):
    if tag == "fixture.server":
        use_fixture(running_server, context)
```

and tag the feature/scenario `@fixture.server`.

## Tags

Tags on Feature/Scenario/Examples select runs:

```bash
behave --tags=@smoke                    # only @smoke
behave --tags="not @wip"                # everything except @wip
behave --tags="@smoke or @wip"
behave --tags="@slow and not @fixme"
```

(behave 1.3+ uses these Cucumber-style tag expressions; the old
`-@tag`/comma syntax is from 1.2.6.)

`behave -w` is the work-in-progress shortcut: only `@wip`, no capture,
stop at first failure.

## Running and CI output

- `behave` runs everything; pass a directory, file, or
  `file.feature:LINE` to narrow to one scenario.
- Useful flags: `--no-capture` (see prints live), `--stop` (first
  failure), `--format=progress` (dense CI logs), `-D key=value` (userdata).
- CI reporting: `behave --junit --junit-directory=reports` emits one XML
  per feature that CI servers ingest directly.
- Defaults live in `behave.ini` / `pyproject.toml` (`[behave]` /
  `[tool.behave]` sections) — put `paths`, default tags, and format there
  rather than in wrapper scripts.

## Step catalog and undefined steps

- Undefined steps don't error out silently: the run summary lists them and
  prints ready-to-paste snippets (`You can implement step definitions for
  undefined steps with these snippets: …`). Snippets use exact phrasing —
  parameterise before committing.
- `behave --steps-catalog` prints every registered step with its location —
  the fast way to check for near-duplicate phrasings before adding a step.
- `behave --dry-run` parses and binds without executing — cheap CI guard
  that every step in every feature is defined.
