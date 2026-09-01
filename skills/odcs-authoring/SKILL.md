---
name: odcs-authoring
description: >-
  Author, edit, and review data contracts in the Open Data Contract Standard
  (ODCS) v3.1.0 — the Bitol / Linux Foundation YAML standard. Covers
  fundamentals, schema objects/properties, logical types, data quality rules
  (library metrics, SQL, custom engines), servers, SLAs, team, roles, and
  foreign-key relationships via references. Use when the user wants to create
  or modify a data contract, mentions ODCS, Bitol, odcs.yaml, or
  datacontract.yaml content, asks to add quality checks / SLAs / schema
  definitions to a contract, to review a contract for completeness, or to
  model a dataset, table, or data product as a contract — even if they just
  say "write a data contract for X".
---

# Authoring ODCS data contracts

Write data contracts against the **Open Data Contract Standard v3.1.0**
(`apiVersion: v3.1.0`), maintained by the Bitol project under the Linux
Foundation. A contract is one YAML document, conventionally named
`<name>.odcs.yaml` (or `datacontract.yaml`).

Start from [assets/template.odcs.yaml](assets/template.odcs.yaml) — copy it
and adapt, rather than writing from a blank page. Validate the result with
`datacontract lint <file>` if the Data Contract CLI is available (see the
`datacontract-cli` skill for the tool itself).

## The shape of a contract

```yaml
apiVersion: v3.1.0        # standard version — always v3.1.0 for new contracts
kind: DataContract
id: 6b1d2c8e-...          # required, unique (UUID recommended)
name: orders_v1
version: 1.0.0            # contract version, semver
status: active            # proposed | draft | active | deprecated | retired
domain: sales
description: {purpose, limitations, usage}
tags: [finance]
schema: [...]             # the structure of the data (objects + properties)
quality: [...]            # usually nested inside schema elements
servers: [...]            # where the data physically lives
slaProperties: [...]      # service-level agreements
team: [...]               # people and ownership
roles: [...]              # access roles for approval workflows
support: [...]            # channels (slack, email, ...)
price: {...}              # optional pricing metadata
customProperties: [...]   # anything org-specific, namespaced
```

`apiVersion`, `kind`, `id`, `version`, and `status` are the only required
fields — but a contract that stops there communicates nothing. A useful
contract has at minimum a described `schema`, an owner in `team`, and the
quality/SLA expectations consumers will rely on.

Notable in v3.1.0: `dataProduct` is deprecated (use domain/name), and a new
**references** mechanism (`schema/<id>/properties/<id>` paths) enables
foreign-key `relationships` — details in the schema reference below.

## Workflow

1. **Gather semantics before syntax.** Identify the objects (tables, topics,
   documents), their properties, ownership, and what consumers depend on:
   freshness, uniqueness, null-tolerance, retention. These become schema,
   quality, and SLA entries.
2. **Write fundamentals** — id, name, version, status, domain, tenant,
   description (purpose/limitations/usage), tags.
3. **Model the schema.** One entry per object; properties with `logicalType`
   (business view) and `physicalType` (implementation view). Add `id` fields
   to elements you will reference (FKs, SLA elements). Read
   [references/schema.md](references/schema.md) for the full field set,
   logical type options, arrays, and relationships.
4. **Attach quality rules** where consumers need guarantees, at object or
   property level. Prefer `library` metrics (`nullValues`, `duplicateValues`,
   `rowCount`, `invalidValues`, `missingValues`) over hand-written SQL —
   engines can execute them portably. Read
   [references/quality-and-sla.md](references/quality-and-sla.md) for
   metrics, operators (`mustBe`, `mustBeLessThan`, …), dimensions, SQL and
   custom-engine rules, and SLA properties.
5. **Declare servers** for each environment the contract protects, then team,
   roles, support, and pricing. Read
   [references/servers-and-metadata.md](references/servers-and-metadata.md)
   for the per-server-type fields and the metadata sections.
6. **Validate.** `datacontract lint <file> --all-errors` against the ODCS
   JSON Schema. Fix errors top-to-bottom; the standard takes precedence over
   the JSON Schema where they disagree.

## Authoring judgment

- **Contract version ≠ apiVersion.** Bump `version` (semver) on contract
  changes: major for breaking (removed/renamed property, tightened type),
  minor for additive. `apiVersion` only changes when adopting a newer
  standard.
- **Platform-agnostic by design.** Keep business meaning in `logicalType`,
  `businessName`, and descriptions; keep engine specifics in `physicalType`
  and `servers`. A consumer on a different platform should still understand
  the contract.
- **Quality rules are promises, not aspirations.** Only encode checks the
  producer will actually stand behind; use `type: text` for intent that
  isn't yet executable.
- **Custom properties over invented fields.** Anything org-specific goes in
  `customProperties` (`- property: ..., value: ...`) — never new top-level
  keys, which fail schema validation.
- **Stable `id`s.** Give objects and properties `id` values when anything
  (relationships, SLAs, other contracts) will point at them — ids survive
  renames; names don't.

## References

- [references/schema.md](references/schema.md) — objects, properties, all
  field definitions, logicalTypeOptions, arrays, dates/timezones, and
  foreign-key relationships.
- [references/quality-and-sla.md](references/quality-and-sla.md) — quality
  rule types and library metrics, comparison operators, scheduling, DQ
  dimensions, and slaProperties.
- [references/servers-and-metadata.md](references/servers-and-metadata.md) —
  server types and their fields, team, roles, support channels, pricing,
  custom properties, authoritative definitions.
- [assets/template.odcs.yaml](assets/template.odcs.yaml) — a complete,
  lint-clean starter contract to copy.
- Authoritative spec: https://github.com/bitol-io/open-data-contract-standard
  (docs/ folder) — consult it for anything not covered here.
