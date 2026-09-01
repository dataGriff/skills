# Data Contract CLI — command reference (v1.x)

Any `[location]` accepts a local path, URL, or S3 URL; it defaults to
`datacontract.yaml`. Global options: `--version`, `--system-truststore`
(corporate proxies/internal CAs), `--config-file <path>` (see testing.md).
Debug any command with `DATACONTRACT_CLI_DEBUG=1`.

## Contents

- [init / edit / lint / changelog](#authoring-commands)
- [test / ci](#test-and-ci)
- [export (formats)](#export)
- [import (sources)](#import)
- [dbt / catalog / publish / api](#other-commands)
- [CI/CD wiring](#cicd-wiring)

## Authoring commands

```bash
datacontract init [location] [--template <url-or-file>] [--overwrite]
    # scaffolds an ODCS v3.1.0 contract with commented-out sections
datacontract edit [location]        # opens the Data Contract Editor web UI
datacontract lint [location] [--all-errors] [--json-schema <url>] \
    [--output <file> --output-format json|junit]
datacontract changelog <v1> <v2>    # human-readable diff incl. breaking changes
```

`lint` stops at the first JSON Schema error by default — use `--all-errors`
when fixing a contract wholesale. `--json-schema` pins a specific ODCS
schema version.

## Test and CI

```bash
datacontract test [location] [--server <name>|all] [--schema-name <obj>|all] \
    [--output <file> --output-format json|junit] [--publish <url>]
datacontract ci <locations...> [--server ...]   # multiple contracts at once
```

`test` reads the contract's `servers` block, connects (credentials from env
vars / config file — see testing.md), and checks: every field present,
types match, `required`/`unique` hold, and all executable quality rules
pass. `ci` is the same engine emitting GitHub Actions annotations and a
step summary, and accepts multiple contract files.

## Export

`datacontract export <format> [location] [--output <file>]` — formats:

| Purpose | Formats |
|---------|---------|
| DDL / models | `sql`, `sql-query`, `bigquery`, `dbml`, `sqlalchemy`, `pydantic-model`, `go`, `spark`, `iceberg` |
| dbt | `dbt-models`, `dbt-sources`, `dbt-staging-sql` |
| Serialization schemas | `avro`, `avro-idl`, `jsonschema`, `protobuf` |
| Quality suites | `sodacl`, `great-expectations`, `dqx`, `data-caterer` |
| Docs | `html`, `markdown`, `mermaid`, `rdf` |
| Contract formats | `odcs`, `dcs` (Data Contract Specification), `excel` (round-trippable template) |
| Anything else | `custom --template <jinja-file>` |

`export sql` supports `--dialect postgres|mysql|snowflake|databricks|sqlserver|trino|oracle|clickhouse`;
without `--dialect` it infers from the contract's `servers` and errors if
there are none.

## Import

`datacontract import <source> --source <path-or-id> [--output <file>]` —
generates a contract (including a `servers` block for live sources, so
`test` works immediately):

- **Files**: `sql` (`--dialect`), `avro`, `jsonschema`, `json`, `csv`,
  `parquet`, `protobuf`, `dbml`, `excel`, `odcs`, `pydantic-model`,
  `spark`, `iceberg`, `powerbi`, `dbt` (manifest)
- **Live systems**: `postgres`, `mysql`, `sqlserver`, `oracle`,
  `snowflake`, `bigquery`, `redshift`, `athena`, `databricks` (Unity
  Catalog), `glue`, `trino`, `s3`, `gcs`, `adls`

Live imports take connection flags (e.g.
`import snowflake --source <account> --database ORDER_DB --schema PUBLIC`);
run `datacontract import <source> --help` for the exact flags.

## Other commands

```bash
datacontract dbt sync [contract] --project-dir <dir>   # write contract tests into dbt project
datacontract dbt test [contract] --project-dir <dir>   # run them via dbt
    # omit the contract to process every *.odcs.yaml in the project
datacontract catalog --files "*.odcs.yaml" --output catalog/   # static HTML catalog
datacontract publish [location]    # publish to Entropy Data (needs API key)
datacontract api                   # REST API server (extra: [api]; POST /lint, /test, ...)
```

## CI/CD wiring

GitHub Actions — use the official action or the CLI directly:

```yaml
- uses: datacontract/datacontract-action@main   # or:
- run: |
    pip install 'datacontract-cli[postgres]'
    datacontract ci contracts/*.odcs.yaml
  env:
    DATACONTRACT_POSTGRES_USERNAME: ${{ vars.DB_USER }}
    DATACONTRACT_POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

Useful patterns:

- PR check: `lint --all-errors` every contract; `changelog` against the
  version on the default branch to surface breaking changes in review.
- Post-deploy: `test` (or `ci`) against the environment just deployed,
  selecting it with `--server`.
- `--output results.json --output-format junit` integrates with test
  reporters.
- Non-zero exit on failure makes all of these gate naturally.
