# Data Contract CLI — connecting `test` to data sources

`datacontract test` connects to whatever the contract's `servers` block
declares. Connection *location* (host, database, …) comes from the
contract; *credentials* come from the environment or a config file — never
put secrets in the contract.

## Credentials via environment variables

Pattern: `DATACONTRACT_<SERVERTYPE>_<OPTION>`. The most used:

| Server type | Variables |
|-------------|-----------|
| postgres | `DATACONTRACT_POSTGRES_USERNAME`, `DATACONTRACT_POSTGRES_PASSWORD` |
| mysql | `DATACONTRACT_MYSQL_USERNAME`, `DATACONTRACT_MYSQL_PASSWORD` |
| sqlserver | `DATACONTRACT_SQLSERVER_USERNAME`, `_PASSWORD`, `_TRUSTED_CONNECTION`, `_AUTHENTICATION` |
| oracle | `DATACONTRACT_ORACLE_USERNAME`, `_PASSWORD`, `_SERVICE_NAME` |
| snowflake | `DATACONTRACT_SNOWFLAKE_USERNAME`, `_PASSWORD` (or `_PRIVATE_KEY`/`_PRIVATE_KEY_FILE` + `_PRIVATE_KEY_FILE_PWD`, `_AUTHENTICATOR`, `_TOKEN`), `_ROLE`, `_WAREHOUSE` |
| bigquery | `DATACONTRACT_BIGQUERY_ACCOUNT_INFO_JSON_PATH` (service-account JSON), `_IMPERSONATION_ACCOUNT`, `_BILLING_PROJECT` |
| databricks | `DATACONTRACT_DATABRICKS_SERVER_HOSTNAME`, `_HTTP_PATH`, `_TOKEN` (or `_CLIENT_ID`/`_CLIENT_SECRET`, `_PROFILE`, `_AUTH_TYPE`) |
| redshift | `DATACONTRACT_REDSHIFT_USERNAME`, `_PASSWORD`, `_AUTHENTICATION`, `_REGION`, `_WORKGROUP` / `_CLUSTER_IDENTIFIER` |
| s3 | `DATACONTRACT_S3_ACCESS_KEY_ID`, `_SECRET_ACCESS_KEY`, `_SESSION_TOKEN`, `_REGION` |
| gcs | `DATACONTRACT_GCS_KEY_ID`, `DATACONTRACT_GCS_SECRET` |
| azure (blob/ADLS) | `DATACONTRACT_AZURE_CONNECTION_STRING` or `_TENANT_ID` + `_CLIENT_ID` + `_CLIENT_SECRET`, `_STORAGE_ACCOUNT_KEY` |
| kafka | `DATACONTRACT_KAFKA_SASL_USERNAME`, `_SASL_PASSWORD`, `_SASL_MECHANISM`, `_SCHEMA_REGISTRY_URL` (+ registry username/password), `_MAX_MESSAGES`, `_TIMEOUT` |
| trino | `DATACONTRACT_TRINO_USERNAME`, `_PASSWORD` or `_JWT_TOKEN`, `_AUTHENTICATION` |
| athena | uses S3/AWS credentials; `DATACONTRACT_ATHENA_STAGING_DIR`, `_CATALOG`, `_SCHEMA` |
| impala | `DATACONTRACT_IMPALA_USERNAME`, `_PASSWORD`, `_AUTH_MECHANISM`, `_USE_SSL`, `_USE_HTTP_TRANSPORT`, `_HTTP_PATH` |

Connection fields like `DATACONTRACT_POSTGRES_HOST`, `_PORT`, `_DATABASE`,
`_SCHEMA` (and equivalents per type) also exist and **override** the
contract's `servers` values when set — useful for pointing tests at a local
stand-in without editing the contract.

For anything not listed, run the failing `test` — errors name the missing
variable — or check the `Config` class in
`datacontract/config/settings.py` (field `snowflake_username` ↔ env var
`DATACONTRACT_SNOWFLAKE_USERNAME`).

## Credentials via config file

`--config-file <path>`, defaulting to `./datacontract-config.yaml` then
`~/.datacontract/config.yaml`. Nested keys join with `_` to form option
names; `${VAR}` interpolates from the environment at load time, so the file
can be committed without secrets:

```yaml
# datacontract-config.yaml
snowflake:
  username: svc_datacontract
  password: ${SNOWFLAKE_PASSWORD}
  role: DATACONTRACT_TEST
  warehouse: TESTING_WH
max_errors: 20
```

Unknown option names fail fast with a ValueError, so typos surface
immediately.

## Extras per source

Install the extra matching the server type (or `[all]`):
`postgres`, `mysql`, `sqlserver`, `oracle`, `snowflake`, `bigquery`,
`databricks`, `redshift`, `athena`, `trino`, `impala`, `s3`, `gcs` (via
`duckdb`), `azure`, `kafka`, `duckdb`, `csv`, `parquet`, `avro`,
`protobuf`, `excel`, `dataframe` (Spark), `iceberg`, `dbml`, `rdf`, `api`.
A missing extra shows up as an import error when testing — install the
extra, don't debug the traceback.

## Local and file-based testing

Files (local, S3, GCS, Azure) are tested through DuckDB — install
`datacontract-cli[duckdb]` (plus `[csv]`/`[parquet]` for those formats).
A `local` server entry makes contract tests runnable offline:

```yaml
servers:
  - server: local
    type: local
    path: ./data/orders.parquet   # globs supported
    format: parquet
```

```bash
datacontract test orders.odcs.yaml --server local
```

The same contract can also declare the production server; select which to
run with `--server`. Testing a Spark DataFrame in a pipeline uses
`type: dataframe` servers with the `[dataframe]` extra and a Spark session
passed via the Python API (`DataContract(..., spark=spark)`).
