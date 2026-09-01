# ODCS v3.1.0 — Schema

The `schema` section describes structure. Terminology:

- **Object** — a structure of data: a table, view, topic, file, document.
- **Property** — an attribute of an object: a column, a field.
- **Element** — either of the above.

```yaml
schema:
  - id: orders_obj            # stable id, used by references/relationships
    name: orders
    logicalType: object
    physicalType: table       # table | view | topic | file | ...
    physicalName: orders_v1
    description: One row per customer order.
    dataGranularityDescription: One row per order_id.
    tags: [sales]
    properties:
      - id: order_id_prop
        name: order_id
        businessName: order identifier
        logicalType: string
        physicalType: uuid
        required: true
        unique: true
        primaryKey: true
        primaryKeyPosition: 1
        classification: internal
        examples: ["b0a3c1f2-..."]
```

## Fields on any element (object or property)

| Key | Notes |
|-----|-------|
| `id` | Optional but recommended when referenced; stable across renames |
| `name` | Required |
| `physicalName`, `physicalType` | Implementation naming/typing |
| `description`, `businessName` | Semantics for humans |
| `authoritativeDefinitions` | Links out (`- url: ..., type: businessDefinition`) |
| `quality` | Array of quality rules (see quality-and-sla.md) |
| `tags`, `customProperties` | Categorisation / org extensions |

Objects additionally take `dataGranularityDescription`.

## Property-specific fields

| Key | Notes |
|-----|-------|
| `logicalType` | `string`, `date`, `timestamp`, `time`, `number`, `integer`, `object`, `array`, `boolean` |
| `logicalTypeOptions` | Constraints per type — see below |
| `required` | May the value be null? default false |
| `unique` | default false |
| `primaryKey`, `primaryKeyPosition` | position from 1 for composite keys |
| `partitioned`, `partitionKeyPosition` | partition columns |
| `classification` | e.g. `public`, `internal`, `restricted`, `confidential` |
| `criticalDataElement` | CDE flag |
| `encryptedName` | name of the column holding the encrypted value |
| `transformSourceObjects`, `transformLogic`, `transformDescription` | lineage |
| `examples` | sample values |
| `items` | schema of array elements (when `logicalType: array`) |
| `relationships` | foreign keys — see below |

## logicalTypeOptions (constraints per logical type)

- **string**: `minLength`, `maxLength`, `pattern` (ECMA-262 regex), `format`
  (`email`, `uuid`, `uri`, `ipv4`, …)
- **integer/number**: `minimum`, `maximum`, `exclusiveMinimum`,
  `exclusiveMaximum`, `multipleOf`, `format` (bit width, Rust-style)
- **date/timestamp/time**: `format` (JDK DateTimeFormatter, e.g.
  `yyyy-MM-dd`), `minimum`/`maximum`/exclusive variants; timestamps also
  `timezone: true|false` and `defaultTimezone` (UTC default)
- **array**: `minItems`, `maxItems`, `uniqueItems`
- **object**: `minProperties`, `maxProperties`, `required` (list of property
  names)

Model temporal precision with `logicalType` + `logicalTypeOptions.format`,
and put the engine-specific type (e.g. `DATETIME`, `TIMESTAMPTZ`) in
`physicalType`.

## Arrays and nesting

```yaml
# array of scalars
- name: street_lines
  logicalType: array
  items:
    logicalType: string

# array of objects
- name: items
  logicalType: array
  items:
    logicalType: object
    properties:
      - {name: sku, logicalType: string}
      - {name: qty, logicalType: integer}
```

## References and relationships (new in v3.1.0)

Reference notation is a slash-separated path over `id` fields:
`schema/<object_id>/properties/<property_id>` (nest deeper with repeated
`/properties/<id>`). Prefix with `<file>#` for another contract:
`customer-contract.yaml#/schema/customers_tbl/properties/cust_id_pk`.
Ids make references refactor-safe — always set `id` on referenced elements.

Currently references power **foreign-key relationships**:

```yaml
# property level — `from` is implicit, must NOT be given
properties:
  - id: customer_id_prop
    name: customer_id
    logicalType: string
    relationships:
      - type: foreignKey            # default, may be omitted
        to: schema/customers_obj/properties/customer_id_prop

# schema (object) level — both from and to required; arrays for composite keys
relationships:
  - from: [schema/orders_obj/properties/tenant_prop, schema/orders_obj/properties/order_prop]
    to: [schema/invoices_obj/properties/tenant_prop, schema/invoices_obj/properties/order_prop]
```

`from`/`to` must match in type (both strings or both equal-length arrays).
