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

`datacontract` is the open-source CLI (Python) for enforcing data
contracts. It natively supports **ODCS v3.x** (v3.1, v3.0; also validates
v2.2.x) — a `.odcs.yaml` file is used directly, no conversion needed. As of
2026 the current release line is 1.x.

## Install

```bash
uv tool install --python python3.12 --upgrade 'datacontract-cli[all]'   # preferred
pip install 'datacontract-cli[all]'                                     # or pip / pipx
docker run --rm -v "${PWD}:/home/datacontract" datacontract/cli:latest  # or docker
```

`[all]` bundles every connector. In constrained environments install only
the extras needed (e.g. `datacontract-cli[postgres]`,
`[snowflake]`, `[databricks]`, `[s3]`, `[duckdb]`, `[kafka]`, `[excel]`,
`[csv]`, `[parquet]`…) — the base install still lints, exports most
formats, and diffs.

## Core loop

```bash
datacontract init orders.odcs.yaml            # scaffold (ODCS v3.1.0 template)
datacontract lint orders.odcs.yaml --all-errors   # validate against ODCS JSON Schema
datacontract test orders.odcs.yaml            # run schema + quality checks on real data
datacontract changelog v1.odcs.yaml v2.odcs.yaml  # diff two versions / breaking changes
datacontract export html orders.odcs.yaml --output orders.html
```

- **lint** checks the YAML against the standard; default stops at the first
  error, `--all-errors` reports everything. Always lint after editing a
  contract, before committing.
- **test** connects to the server(s) in the contract's `servers` block and
  verifies real data: fields present, types match, quality rules pass.
  Credentials come from `DATACONTRACT_<TYPE>_*` environment variables or a
  `datacontract-config.yaml` — see
  [references/testing.md](references/testing.md) before running tests.
  Select one server with `--server <name>`, one object with
  `--schema-name <name>`.
- **changelog** shows what changed between two contract versions, flagging
  breaking changes — run it before bumping the contract version to decide
  major vs minor.
- **export/import** use subcommands per format:
  `datacontract export sql --dialect postgres orders.odcs.yaml`,
  `datacontract import sql --source ddl.sql --dialect postgres --output orders.odcs.yaml`.
  Full format lists, dbt sync, and CI patterns:
  [references/commands.md](references/commands.md).

## Practical notes

- Contract locations can be local paths, URLs, or S3 URLs in any command.
- `export sql` infers the dialect from the contract's `servers`; with no
  servers defined it errors — pass `--dialect` explicitly.
- Use `--output <file>` rather than shell redirection (the Docker image
  wraps stdout at 80 columns).
- `datacontract ci <files...>` is `test` tuned for pipelines: GitHub
  Actions annotations and step summaries. A GitHub Action wrapper exists at
  github.com/datacontract/datacontract-action.
- Bootstrapping from existing data is usually faster than hand-writing:
  `datacontract import <source>` against a live database also generates the
  `servers` block, so `test` works immediately afterwards.
- Behind a corporate proxy/internal CA, pass `--system-truststore`.
- Python API: `from datacontract.data_contract import DataContract;
  DataContract(data_contract_file="orders.odcs.yaml").test().has_passed()`.

Exit codes are non-zero on failed lint/test — safe to gate pipelines on.
When a gated `test` fails, fix the data or the producing pipeline, or
renegotiate the contract with its owners and bump its version — never
quietly loosen the contract to get a pipeline green: the contract records
an agreement, and weakening it silently breaks every consumer relying on it.

For writing the contract YAML itself (schema, quality rules, SLAs), use the
`odcs-authoring` skill.

## References

- [references/commands.md](references/commands.md) — full command
  reference: every command with options, all export/import formats, dbt
  workflow, catalog/publish/api, CI/CD wiring.
- [references/testing.md](references/testing.md) — connecting `test` to
  data sources: credential environment variables, config file format,
  extras per source, local file testing via DuckDB.
