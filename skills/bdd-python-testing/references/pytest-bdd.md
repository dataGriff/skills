# pytest-bdd mechanics

Details beyond the core shape in SKILL.md. Applies to pytest-bdd 7+/8+
(noted where behaviour differs).

## Contents

- [Binding scenarios](#binding-scenarios)
- [Parsers and custom types](#parsers-and-custom-types)
- [Sharing state and steps](#sharing-state-and-steps)
- [Data tables and docstrings](#data-tables-and-docstrings)
- [Scenario outlines](#scenario-outlines)
- [Tags and hooks](#tags-and-hooks)
- [Configuration](#configuration)
- [Finding and generating missing steps](#finding-and-generating-missing-steps)

## Binding scenarios

Two ways to bind a feature file to a test module:

```python
from pytest_bdd import scenario, scenarios

# All scenarios in the file(s) — the default choice.
scenarios("features/withdrawal.feature")
scenarios("features/")            # every .feature under the directory

# One scenario, when you need a wrapper to add markers or docs.
@scenario("features/withdrawal.feature", "Withdrawal exceeding the balance")
def test_overdraw():
    pass  # body runs AFTER all scenario steps; usually empty
```

Paths are relative to the test file (or to `bdd_features_base_dir`, see
Configuration). `scenarios()` skips any scenario already bound manually
with `@scenario` in the same module, so the two can be mixed.

## Parsers and custom types

The default matcher is an exact string. For parameters, wrap the pattern:

```python
from pytest_bdd import parsers

@when(parsers.parse("Alice withdraws £{amount:d}"))      # parse-format
@when(parsers.cfparse("{count:Number} items", extra_types={"Number": int}))
@when(parsers.re(r"Alice withdraws £(?P<amount>\d+)", converters={"amount": int}))
```

- `parse` — format-string style; `{amount:d}` converts to int, `{name}`
  captures a string (non-greedy to the next literal).
- `cfparse` — like `parse` plus cardinality (`{items:Item+}` captures a
  list); needs `extra_types` for custom type names.
- `re` — full regex; named groups become arguments, `converters` maps them
  from string.

Pick one flavour per project and stick to it. A step decorated with a bare
string matches only that exact text.

Custom conversions belong in the parser (`extra_types` / `converters`),
not repeated inside step bodies.

## Sharing state and steps

- `target_fixture="name"` on a `@given`/`@when` makes the step's return
  value a fixture other steps inject by argument name. This is the only
  sanctioned state channel; it overrides an existing fixture of the same
  name for the scenario's duration — which is also the idiom for a Given
  that replaces a default fixture (e.g. an authenticated client over an
  anonymous one).
- Steps defined in `conftest.py` are visible to all test modules below it —
  put cross-feature steps (login, common setup) there, feature-specific
  steps next to their binding module.
- Ordinary pytest fixtures work in steps as usual; `autouse` fixtures and
  fixture finalizers are the cleanup mechanism (there is no Gherkin
  teardown).
- One step function can serve several phrasings by stacking decorators
  (e.g. the same function as `@given("...")` and `@when("...")`).

## Data tables and docstrings

pytest-bdd 8+ passes a step's table as the `datatable` argument (list of
row lists, header included) and its docstring as `docstring` (string):

```gherkin
Given the following accounts:
  | owner | balance |
  | Alice | 100     |
  | Bob   | 40      |
```

```python
@given("the following accounts:", target_fixture="accounts")
def accounts(datatable):
    header, *rows = datatable
    return [Account(**dict(zip(header, row))) for row in rows]
```

On pytest-bdd 7.x these arguments don't exist — the table text is part of
the step name and must be parsed from it; prefer upgrading over writing
that parser.

## Scenario outlines

Nothing special is needed: each Examples row becomes a separate pytest
test, and the substituted values are matched by the ordinary parsers.
Ensure the parser type matches the example values (`{amount:d}` fails on a
row with `12.50` — use `{amount:g}` or a converter).

## Tags and hooks

- Gherkin tags become pytest markers: `@smoke` on a Feature/Scenario →
  `pytest -m smoke`. Register each tag in the `markers` ini section to
  avoid unknown-marker warnings.
- Hooks are pytest plugin hooks in `conftest.py`:
  `pytest_bdd_before_scenario`, `pytest_bdd_after_scenario`,
  `pytest_bdd_before_step`, `pytest_bdd_after_step`,
  `pytest_bdd_step_error(request, feature, scenario, step, step_func,
  step_func_args, exception)`. Use them for logging/screenshots, not for
  test logic — state setup belongs in fixtures.

## Configuration

In `pytest.ini` / `pyproject.toml` (`[tool.pytest.ini_options]`):

```ini
bdd_features_base_dir = tests/features
```

makes `scenarios("withdrawal.feature")` resolve from that directory —
worth setting once the tree has more than one test package.

## Finding and generating missing steps

An unbound step fails the scenario with a `StepDefinitionNotFoundError`
naming the step. To get stub definitions for everything unbound:

```bash
pytest --generate-missing --feature tests/features tests/
```

which prints skeleton functions to paste in. Generated stubs use exact
string matchers — parameterise them with parsers before committing.
