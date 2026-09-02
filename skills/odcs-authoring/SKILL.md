---
name: odcs-authoring
description: >-
  Author, edit, and review data contracts in the Open Data Contract Standard
  (ODCS) v3.1.0 — the Bitol / Linux Foundation YAML standard. Covers
  fundamentals, schema objects/properties, logical types, data quality rules
  (library metrics, SQL, custom engines), servers, SLAs, team, roles,
  foreign-key relationships via references, lower_snake_case naming
  conventions, and enforcing org style rules with Spectral rulesets. Use
  when the user wants to create or modify a data contract, mentions ODCS,
  Bitol, odcs.yaml, or datacontract.yaml content, asks to add quality
  checks / SLAs / schema definitions to a contract, to review a contract
  for completeness or convention compliance, to lint contracts with
  Spectral, or to model a dataset, table, or data product as a contract —
  even if they just say "write a data contract for X".
---

# Authoring ODCS data contracts

A contract is one YAML document against the **Open Data Contract Standard
v3.1.0** (`apiVersion: v3.1.0`), conventionally `<name>.odcs.yaml`. The
skeleton below carries the syntax for everything a useful contract needs;
work from it directly and open the references only for the cases listed at
the end. Validate with `datacontract lint <file> --all-errors` when the
Data Contract CLI is installed (the `datacontract-cli` skill covers it).

## The skeleton

```yaml
apiVersion: v3.1.0
kind: DataContract
id: 6b1d2c8e-0c1e-4c0f-9c2a-1d2e3f4a5b6c   # required, stable; a UUID
name: orders_v1
version: 1.0.0            # contract semver; major = breaking change
status: active            # proposed | draft | active | deprecated | retired
domain: sales
description:
  purpose: Curated order data for analytics and finance reporting.
  limitations: Not for operational use. PII columns are restricted.
  usage: Refreshed hourly; join on order_id.
tags: [orders, sales]

schema:
  - id: orders_obj
    name: orders                      # lower_snake_case, always
    logicalType: object
    physicalType: table
    description: One row per customer order.
    properties:
      - id: order_id_prop
        name: order_id
        businessName: Order identifier   # human casing lives here
        description: Unique identifier of the order.
        logicalType: string             # business view
        physicalType: uuid              # implementation view
        required: true
        unique: true
        primaryKey: true
        quality:
          - id: order_id_no_nulls
            metric: nullValues
            mustBe: 0
      - id: order_status_prop
        name: order_status
        description: Current lifecycle state of the order.
        logicalType: string
        physicalType: text
        required: true
        quality:
          - id: order_status_valid
            metric: invalidValues
            arguments:
              validValues: [pending, paid, shipped, cancelled, refunded]
            mustBe: 0
    quality:
      - id: orders_row_count
        metric: rowCount
        mustBeGreaterThan: 0

servers:
  - server: production
    type: postgres
    environment: prod
    host: analytics-db.example.com
    port: 5432
    database: warehouse
    schema: mart_sales                # never credentials — reference a secret store

slaProperties:
  - id: freshness
    property: latency               # also: frequency, retention,
    value: 2                        #   timeOfAvailability, generalAvailability,
    unit: h                         #   endOfSupport, endOfLife
    element: orders.created_at
  - id: retention
    property: retention
    value: 5
    unit: y

team:                               # object form; a bare list is deprecated
  name: Sales Analytics
  members:
    - username: priya@example.com
      role: owner
support:
  - channel: "#sales-data"
    tool: slack
    scope: interactive
```

`apiVersion`, `kind`, `id`, `version`, `status` are the only required
fields; a contract that stops there communicates nothing. A useful one has
a described schema, an owner in `team`, and the quality and SLA promises
consumers will rely on.

## Rules that matter

- **Names are lower_snake_case** for objects and properties — they flow
  into SQL, dbt, and Avro via exporters and snake_case survives every
  target. Human-friendly casing belongs in `businessName`.
- **Quality rules are promises.** Prefer library metrics (`nullValues`,
  `duplicateValues`, `rowCount`, `invalidValues`, `missingValues`) with
  `mustBe` / `mustBeLessThan` / `mustBeGreaterThan` / `mustBeBetween` over
  hand-written SQL; only encode checks the producer will stand behind.
  Use `type: text` for intent that isn't executable yet.
- **v3.1.0 migration traps** when reviewing older contracts: `dataProduct`
  is deprecated (use `domain` + `name`); quality `rule:` became `metric:`
  (or `type: sql` / `type: custom`); `team` is an object with `members`,
  not a list; credentials never belong in `servers`.
- **Contract version ≠ apiVersion.** Bump `version` on contract changes
  (major for removed/renamed properties or tightened types, minor for
  additive); `apiVersion` only changes when adopting a newer standard.
- **Business meaning vs engine detail.** `logicalType`, `businessName`,
  descriptions carry meaning; `physicalType` and `servers` carry platform
  specifics, so a consumer on another platform still understands it.
- **Org-specific data goes in `customProperties`** (`- property: …,
  value: …`) — never invented top-level keys, which fail validation.
- **Give `id`s to anything referenced** (relationships, SLA `element`s,
  other contracts): ids survive renames, names don't.

## Workflow

1. Gather semantics first: objects, properties, ownership, and what
   consumers depend on (freshness, uniqueness, null-tolerance, retention).
2. Fill the fundamentals, then the schema with both logical and physical
   types and descriptions on every element.
3. Attach quality rules where consumers need guarantees; declare SLAs;
   add servers per environment, then team and support.
4. Lint, fix top-to-bottom (the standard wins over the JSON Schema where
   they disagree), and bump `version` if this replaces an existing contract.

## When to open the references

- [references/schema.md](references/schema.md) — arrays, nested objects,
  `logicalTypeOptions`, dates/timezones, foreign-key `relationships` via
  `schema/<id>/properties/<id>` references.
- [references/quality-and-sla.md](references/quality-and-sla.md) — SQL and
  custom-engine rules, scheduling, DQ dimensions, the full SLA property
  list.
- [references/servers-and-metadata.md](references/servers-and-metadata.md)
  — fields for non-postgres server types, roles, pricing, authoritative
  definitions.
- [references/style-and-governance.md](references/style-and-governance.md)
  with [assets/spectral-odcs.yaml](assets/spectral-odcs.yaml) — only when
  setting up or extending Spectral linting of org conventions in CI.
- [assets/template.odcs.yaml](assets/template.odcs.yaml) — a fuller
  lint-clean example (dates with formats, granularity, member dates) if
  the skeleton isn't enough.
- Authoritative spec: https://github.com/bitol-io/open-data-contract-standard
