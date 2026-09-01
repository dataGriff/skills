# ODCS v3.1.0 — Servers, Team, Roles, Support, Pricing, Custom Properties

## Servers

`servers` says where the data physically lives — one entry per
dataset-on-environment. Common fields:

```yaml
servers:
  - server: production        # required identifier
    id: prod_server           # optional stable id
    type: postgres            # required, see list below
    description: Primary replica
    environment: prod         # prod | preprod | uat | dev | ...
    # ...type-specific fields...
    roles: [...]              # roles with access to this server
    customProperties: [...]
```

Valid `type` values: `api`, `athena`, `azure`, `bigquery`, `clickhouse`,
`cloudsql`, `custom`, `databricks`, `db2`, `denodo`, `dremio`, `duckdb`,
`glue`, `hive`, `impala`, `informix`, `kafka`, `kinesis`, `local`, `mysql`,
`oracle`, `postgres`/`postgresql`, `presto`, `pubsub`, `redshift`, `s3`,
`sftp`, `snowflake`, `sqlserver`, `synapse`, `trino`, `vertica`, `zen`.

Type-specific fields for the most common types (full tables:
`docs/infrastructure-servers.md` in the bitol-io/open-data-contract-standard
repo):

| type | required fields | notable optional |
|------|-----------------|------------------|
| postgres/mysql/sqlserver/db2 | `host`, `port`, `database` | `schema` |
| snowflake | `host`, `account`, `database`, `schema` | `warehouse`, `role` |
| bigquery | `project`, `dataset` | |
| databricks | `catalog`, `schema` | `host` |
| athena | `schema` | `stagingDir`, `catalog`, `regionName` |
| glue | `account`, `database` | `location`, `format` |
| s3/azure | `location` (path/URL, globs ok), format for azure | `format`, `delimiter` |
| kafka | `host` (bootstrap server) | `format` (e.g. avro, json) |
| duckdb | `database` (file path) | `schema` |
| local | `path`, `format` | |
| api | `location` (URL) | |
| custom | free-form | use when your platform isn't listed |

## Team (structure changed in v3.1.0)

`team` is now an **object** with a `members` list (shared Bitol RFC 0016
structure). The v2.x/v3.0 flat-array form still validates but is deprecated
and will be removed in ODCS v4 — author the new form:

```yaml
team:
  id: orders_team
  name: Orders Squad
  description: Owns the orders data product.
  members:
    - username: jdoe@example.com   # required per member
      name: Jane Doe
      role: owner                  # free-form: owner, data steward, ...
      dateIn: 2024-01-15
    - username: former@example.com
      role: engineer
      dateIn: 2023-01-01
      dateOut: 2024-06-01
      replacedByUsername: jdoe@example.com
```

## Roles

IAM roles that grant access to the dataset, with approval chain metadata:

```yaml
roles:
  - role: orders_read          # required: IAM role name
    access: read
    description: Read access for analysts.
    firstLevelApprovers: Reporting Manager
    secondLevelApprovers: data-platform-lead
```

## Support channels

```yaml
support:
  - channel: "#orders-data"        # required
    tool: slack                    # email | slack | teams | discord | ticket | googlechat | other
    scope: interactive             # interactive | announcements | issues | notifications
    url: https://myorg.slack.com/archives/C012345
  - channel: orders-announce
    tool: email
    scope: announcements
    url: mailto:orders-data@example.com
    invitationUrl: https://...     # for subscribe/request flows
```

## Pricing

```yaml
price:
  priceAmount: 9.95
  priceCurrency: USD
  priceUnit: megabyte
```

## Custom properties

Available in most sections and at top level; the escape hatch for anything
org-specific — never invent non-standard keys elsewhere:

```yaml
customProperties:
  - property: dataprocClusterName   # camelCase name
    value: cluster-17               # any type, arrays allowed
    description: Cluster for enrichment jobs.
    id: dataproc_cluster            # since v3.1, use id for referencing
```

## Authoritative definitions

Shared block linking out to catalogs, docs, videos — usable on the contract,
description, schema elements, quality rules, and team:

```yaml
authoritativeDefinitions:
  - url: https://catalog.example.com/dataset/orders
    type: businessDefinition
    description: Catalog entry.
```

Common `type` values: `businessDefinition`, `transformationImplementation`,
`videoTutorial`, `tutorial`, `implementation`.
