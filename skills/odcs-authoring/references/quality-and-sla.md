# ODCS v3.1.0 — Data Quality and SLAs

## Quality rules

`quality` is an array attached to a schema object (table-level checks) or a
property (column-level checks). Four rule types:

| `type` | Meaning |
|--------|---------|
| `library` (default) | Predefined, engine-portable metric — prefer this |
| `text` | Human-readable expectation, not (yet) executable |
| `sql` | A query returning a number/boolean to compare |
| `custom` | Vendor block passed as-is to an engine (Soda, Great Expectations, …) |

`type: library` may be omitted when `metric` is present. (`rule` is the
deprecated pre-3.1 name for `metric`.)

### Library metrics (improved in v3.1.0)

| Metric | Level | Arguments |
|--------|-------|-----------|
| `nullValues` | property | — |
| `missingValues` | property | `missingValues: [null, '', 'N/A']` |
| `invalidValues` | property | `validValues: [...]` or `pattern: '<regex>'` |
| `duplicateValues` | property | — |
| `duplicateValues` | schema | `properties: [tenant_id, order_id]` (compound uniqueness) |
| `rowCount` | schema | — |

Metrics return a number compared via an operator, in `unit: rows` (default)
or `unit: percent`:

```yaml
properties:
  - name: order_id
    quality:
      - id: order_id_no_nulls
        metric: nullValues
        mustBe: 0
        description: There must be no null values.
      - id: order_id_format
        metric: invalidValues
        arguments:
          pattern: '^ORD-[0-9]{8}$'
        mustBe: 0
```

Schema-object-level checks (e.g. `rowCount`) use the same `quality` key,
attached to the schema object instead of a property:

```yaml
schema:
  - name: orders
    quality:
      - id: orders_row_count
        metric: rowCount
        mustBeBetween: [100, 120]
```

### Comparison operators

`mustBe` (=), `mustNotBe` (≠), `mustBeGreaterThan` (>),
`mustBeGreaterOrEqualTo` (≥), `mustBeLessThan` (<), `mustBeLessOrEqualTo`
(≤), `mustBeBetween: [lo, hi]`, `mustNotBeBetween: [lo, hi]`.

### SQL rules

`{object}` and `{property}` are substituted with the current element's
physical names. Write the query in the dialect of the contract's server.

```yaml
quality:
  - id: freshness_1h
    type: sql
    query: |
      SELECT EXTRACT(EPOCH FROM NOW() - MAX(updated_at)) FROM {object}
    mustBeLessThan: 3600
```

### Custom rules

```yaml
quality:
  - id: soda_duplicate_percent
    type: custom
    engine: soda            # soda | greatExpectations | montecarlo | ...
    implementation: |
      type: duplicate_percent
      columns: [carrier, shipment_number]
      must_be_less_than: 1.0
```

### Other quality fields

- `dimension`: one of `accuracy`, `completeness`, `conformity`,
  `consistency`, `coverage`, `timeliness`, `uniqueness` — for DQ reporting.
- `severity`, `businessImpact` — consequence metadata.
- `scheduler: cron` + `schedule: "0 20 * * *"` — execution scheduling
  (replaces pre-3.1 `scheduleCronExpression`).
- `name`, `description`, `tags`, `customProperties`,
  `authoritativeDefinitions` as elsewhere.

## Service-level agreements

Top-level `slaProperties`: a list of `property`/`value` pairs following the
Data QoS vocabulary. `element` targets `object.property` notation (omit the
object when the contract has only one).

```yaml
slaProperties:
  - id: freshness
    property: latency        # preferred over "freshness"
    value: 4
    unit: h
    element: orders.order_timestamp
  - property: frequency      # update cadence
    value: 1
    unit: d
  - property: retention
    value: 3
    unit: y
  - property: generalAvailability
    value: 2025-05-12T09:30:10-08:00
  - property: timeOfAvailability
    value: 09:00-08:00
    driver: regulatory       # regulatory | analytics | operational
```

Recommended `property` values (case-insensitive): `availability`,
`throughput`, `errorRate`, `generalAvailability`, `endOfSupport`,
`endOfLife`, `retention`, `frequency`, `latency`, `timeToDetect`,
`timeToNotify`, `timeToRepair`. Units are ISO-style (`d`/`day`, `y`/`yr`,
etc.). `slaDefaultElement` is deprecated since v3.1.0.
