# ODCS — naming conventions and Spectral governance

`datacontract lint` validates against the ODCS JSON Schema — structure, not
style. It will happily accept `orderId`, a missing owner, or undescribed
columns. Org conventions need a second linter: **Spectral**
(https://stoplight.io/open-source/spectral), a general YAML/JSON linter
with custom rulesets. There is no official Bitol ruleset — each org writes
its own; this skill ships a working starter.

## Naming conventions

Use **lower_snake_case** for schema object and property `name` values (and
`physicalName` where the platform allows). Reasons:

- Names flow into SQL DDL, dbt models, Avro fields, and quality-check SQL
  via exporters — snake_case survives every target; camelCase gets mangled
  by case-insensitive engines (Snowflake upper-cases unquoted identifiers).
- Contracts diff and review better when producer and consumer never argue
  about casing.

Put human-friendly casing in `businessName` ("Order Identifier"), not in
`name`. Also keep quality rule `id`s, schema `id`s, and server names
snake_case — they end up in reference paths and reports.

## Spectral setup

```bash
npm install -g @stoplight/spectral-cli   # or npx @stoplight/spectral-cli
spectral lint --ruleset spectral-odcs.yaml "contracts/**/*.odcs.yaml"
```

Copy [../assets/spectral-odcs.yaml](../assets/spectral-odcs.yaml) as the
starting ruleset. What it enforces (adapt severities to taste):

| Rule | Severity | Checks |
|------|----------|--------|
| `odcs-api-version` | error | `apiVersion` matches `v3.x.x` |
| `object-name-snake-case` | error | object names lower_snake_case |
| `property-name-snake-case` | error | property names (nested too) lower_snake_case |
| `object-must-have-description` | error | every object described |
| `property-must-have-description` | warn | every property described |
| `contract-must-have-owner` | error | `team` present |
| `contract-must-have-slas` | warn | `slaProperties` present |
| `status-valid-values` | error | status in the lifecycle set |
| `no-secrets-in-servers` | error | no `password` field on servers |

## Writing your own rules

Spectral rules are JSONPath (`given`) + a function (`then`). The functions
that matter for contracts: `casing` (types: `snake`, `camel`, `kebab`,
`pascal`), `pattern`, `truthy`, `undefined`, `enumeration`, `length`,
`schema`. Examples:

```yaml
# every quality rule must have an id (needed for stable references)
quality-rules-need-ids:
  severity: error
  given: $..quality[*]
  then:
    field: id
    function: truthy

# classification must come from the org taxonomy
classification-taxonomy:
  severity: error
  given: $.schema[*]..properties[*].classification
  then:
    function: enumeration
    functionOptions:
      values: [public, internal, restricted, confidential]
```

Nested properties need the recursive path (`$.schema[*]..properties[*]`),
not `$.schema[*].properties[*]` — arrays of objects nest `properties`
arbitrarily deep.

## CI wiring

Run both linters on every contract change; they catch disjoint problems:

```yaml
- run: |
    pip install datacontract-cli
    npm install -g @stoplight/spectral-cli
    datacontract lint contracts/orders.odcs.yaml --all-errors
    spectral lint --ruleset spectral-odcs.yaml "contracts/**/*.odcs.yaml"
```

Spectral exits non-zero on `error`-severity findings (add
`--fail-severity warn` to gate on warnings too), so both gate naturally.
In a Taskfile-driven repo, wrap the pair in one `check:contracts` task and
call it from `ci`.
