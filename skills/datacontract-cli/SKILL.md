---
name: datacontract-cli
description: >-
  Operate the Data Contract CLI (`datacontract`, datacontract.com) to
  enforce data contracts: init, lint, test data against real sources
  (Postgres, Snowflake, BigQuery, Databricks, S3, Kafka, ...), export to 25+
  formats (SQL DDL, dbt, Avro, JSON Schema, HTML, Excel, ...), import
  contracts from existing schemas, diff/changelog versions, sync dbt tests,
  and wire contracts into CI/CD. Use when the user mentions the datacontract
  command or datacontract-cli, wants to validate/lint/test a data contract
  or check real data against one, convert a contract to/from another format,
  generate a contract from an existing database or schema, or automate
  contract checks in a pipeline. Pairs with the odcs-authoring skill for
  writing the contract content itself.
---

# Data Contract CLI

`datacontract` is the open-source Python CLI for enforcing data contracts.
It reads **ODCS v3.x** (`.odcs.yaml`) directly; the current release line
is 1.x. Everything below is enough for the everyday commands — open the
references only for the cases listed at the end.

## Install

```bash
uv tool install --python python3.12 --upgrade 'datacontract-cli[all]'   # preferred
pip install 'datacontract-cli[all]'                                     # or pip / pipx
docker run --rm -v "${PWD}:/home/datacontract" datacontract/cli:latest  # or docker
```

`[all]` bundles every connector; in constrained environments install only
the extra matching the source (`[postgres]`, `[snowflake]`, `[bigquery]`,
`[databricks]`, `[s3]`, `[duckdb]`, `[kafka]`, `[csv]`, `[parquet]`…).
The base install still lints, exports most formats, and diffs. A missing
extra surfaces as an import error when testing — install it, don't debug.

## Core loop

```bash
datacontract init orders.odcs.yaml                  # scaffold (ODCS v3.1.0)
datacontract lint orders.odcs.yaml --all-errors     # validate; default stops at first error
datacontract test orders.odcs.yaml [--server prod] [--schema-name orders]
datacontract changelog v1.odcs.yaml v2.odcs.yaml    # diff, flags breaking changes
datacontract export html orders.odcs.yaml --output orders.html
datacontract ci contracts/*.odcs.yaml               # test, tuned for pipelines
```

Lint after every edit. `test` connects to the contract's `servers` and
checks fields present, types match, `required`/`unique` hold, quality
rules pass. `changelog` before bumping a version decides major vs minor.
Non-zero exit on failed lint/test — safe to gate pipelines on.

## Credentials for `test` and `ci`

Never in the contract. Env vars follow `DATACONTRACT_<SERVERTYPE>_<OPTION>`:

| Source | Variables |
|--------|-----------|
| postgres / mysql | `DATACONTRACT_POSTGRES_USERNAME`, `_PASSWORD` (mysql likewise) |
| snowflake | `DATACONTRACT_SNOWFLAKE_USERNAME` + `_PASSWORD`, or key-pair: `_PRIVATE_KEY` / `_PRIVATE_KEY_FILE` (+ `_PRIVATE_KEY_FILE_PWD`); `_ROLE`, `_WAREHOUSE` |
| bigquery | `DATACONTRACT_BIGQUERY_ACCOUNT_INFO_JSON_PATH` (service-account JSON) |
| databricks | `DATACONTRACT_DATABRICKS_SERVER_HOSTNAME`, `_HTTP_PATH`, `_TOKEN` |
| s3 | `DATACONTRACT_S3_ACCESS_KEY_ID`, `_SECRET_ACCESS_KEY`, `_REGION` |

Connection fields (`DATACONTRACT_POSTGRES_HOST`, `_DATABASE`, …) also
exist and override the contract's `servers` when set. Alternatively a
`datacontract-config.yaml` (`--config-file`) with nested keys and
`${VAR}` interpolation, committable without secrets. Other sources
(sqlserver, oracle, redshift, kafka, trino, athena, gcs, azure…) and
local/file testing via DuckDB: [references/testing.md](references/testing.md).

## Export and import

```bash
datacontract export <format> orders.odcs.yaml --output <file>
datacontract import <source> --source <path-or-id> --output orders.odcs.yaml
```

Export formats: `sql` (`--dialect postgres|snowflake|databricks|…`;
inferred from `servers`, errors without either), `dbt-models`,
`dbt-sources`, `dbt-staging-sql`, `avro`, `jsonschema`, `protobuf`,
`html`, `markdown`, `sodacl`, `great-expectations`, `pydantic-model`,
`spark`, `bigquery`, `excel`, `odcs`, `custom --template <jinja>`.
Import sources: files `sql` (`--dialect`), `avro`, `jsonschema`, `csv`,
`parquet`, `excel`, `dbt` (manifest), and live systems `postgres`,
`snowflake`, `bigquery`, `databricks`, `s3`, `glue`… — live imports also
generate the `servers` block, so `test` works immediately; run
`datacontract import <source> --help` for connection flags. The complete
lists, `dbt sync`/`dbt test`, `catalog`, `publish`, and `api`:
[references/commands.md](references/commands.md) when a format or command
isn't above.

## CI wiring

```yaml
- run: |
    pip install 'datacontract-cli[postgres]'
    datacontract lint --all-errors contracts/*.odcs.yaml
    datacontract ci contracts/*.odcs.yaml
  env:
    DATACONTRACT_POSTGRES_USERNAME: ${{ vars.DB_USER }}
    DATACONTRACT_POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

`datacontract ci` emits GitHub Actions annotations and a step summary;
`datacontract/datacontract-action` wraps it. PR checks lint every contract
and run `changelog` against the default branch's version; post-deploy runs
`test --server <env>`. `--output results.xml --output-format junit` feeds
test reporters.

## Practical notes

- Contract locations can be local paths, URLs, or S3 URLs in any command.
- Use `--output <file>` rather than shell redirection (the Docker image
  wraps stdout at 80 columns).
- Behind a corporate proxy or internal CA, pass `--system-truststore`.
  Debug any command with `DATACONTRACT_CLI_DEBUG=1`.
- Python API: `from datacontract.data_contract import DataContract;
  DataContract(data_contract_file="orders.odcs.yaml").test().has_passed()`.
- For the contract YAML itself (schema, quality rules, SLAs), use the
  `odcs-authoring` skill.

## When to open the references

- [references/commands.md](references/commands.md) — every option of every
  command, the full export/import lists, dbt sync, catalog, publish, api.
- [references/testing.md](references/testing.md) — credentials for sources
  not in the table above, the config-file format, extras per source, and
  local/file-based testing through DuckDB.
