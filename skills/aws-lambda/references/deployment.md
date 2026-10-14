# Packaging and deployment

## Packaging: zip vs container image

Zip is the default: fastest cold starts, simplest builds. Limits: 50 MB
zipped upload (larger via S3), 250 MB unzipped including layers. Switch to a
**container image** (up to 10 GB) only when deps outgrow that (ML libs,
native binaries) or the org standardises on images — base images
`public.ecr.aws/lambda/python:3.13` etc. keep the runtime interface client
wired; `CMD ["app.handler"]` names the handler. Images cold-start slower on
first pull but are cached aggressively after.

Dependencies must be built for the target platform (Linux, matching
`Architectures`). `sam build` handles this (add `--use-container` when
native extensions misbehave); raw zips need
`pip install --platform manylinux2014_aarch64 --only-binary=:all: -t .` or a
Docker build — a macOS-built `.so` in a zip is the classic
`Runtime.ImportModuleError`.

## Layers

Layers share libraries/binaries across functions and slim the function zip;
contents land under `/opt` (Python: `python/` prefix in the layer zip; Node:
`nodejs/node_modules/`). They still count toward the 250 MB unzipped limit,
and they version independently — pin exact layer version ARNs in IaC.
Use them for shared internal libs and the Powertools/collector layers AWS
publishes; don't use them to dodge dependency management (the function
still can't import what its runtime can't resolve).

## SAM workflow

```bash
sam build [--use-container]      # resolves deps into .aws-sam/
sam validate --lint              # template check (cfn-lint rules)
sam deploy --guided              # first deploy: writes samconfig.toml
sam deploy                       # thereafter
sam logs -n OrdersFunction --tail
sam delete                       # tear down the stack
```

Local execution (needs Docker): `sam local invoke OrdersFunction -e
event.json`, `sam local start-api` (HTTP events), `sam local
start-lambda` (SDK-invokable endpoint). It emulates the runtime, not IAM or
timeouts — an execution-role bug still only shows in a deployed stack.
`sam sync --watch` hot-syncs code changes to a dev stack in seconds,
bypassing CloudFormation for code-only edits (dev environments only).

## CDK

```typescript
const fn = new lambda.Function(this, "Orders", {
  runtime: lambda.Runtime.PYTHON_3_13,
  architecture: lambda.Architecture.ARM_64,
  handler: "app.handler",
  code: lambda.Code.fromAsset("src"),
  timeout: cdk.Duration.seconds(30),
  memorySize: 512,
});
table.grantReadWriteData(fn);      // grants build the least-privilege role
```

Prefer `NodejsFunction` / `PythonFunction` constructs (they bundle deps via
esbuild/Docker). `grant*` methods on resources beat hand-writing policy
statements. `cdk deploy --hotswap` is SAM sync's equivalent for dev loops.

## Terraform

`aws_lambda_function` needs the pieces SAM implies. Minimum set:
`archive_file` data source (or external build step) for the zip,
`source_code_hash = data.archive_file.zip.output_base64sha256` so code
changes actually redeploy, an `aws_iam_role` with
`AWSLambdaBasicExecutionRole` attached, and one `aws_lambda_permission` per
service allowed to invoke. For queue/stream triggers use
`aws_lambda_event_source_mapping` (with `function_response_types =
["ReportBatchItemFailures"]`). The `terraform-aws-modules/lambda/aws` module
handles build+package and is widely used — fine to adopt when the repo
already uses community modules.

## Versions, aliases, gradual deploys

`$LATEST` is mutable; production traffic should target an **alias** (e.g.
`live`) pointing at a published, immutable version. Aliases enable weighted
traffic shifting between two versions. In SAM this is declarative:

```yaml
AutoPublishAlias: live
DeploymentPreference:
  Type: Canary10Percent5Minutes    # or Linear10PercentEvery1Minute, AllAtOnce
  Alarms: [!Ref ErrorsAlarm]       # auto-rollback trigger
```

CodeDeploy shifts traffic and rolls back if the alarm fires. Provisioned
concurrency and SnapStart also attach to versions/aliases, never `$LATEST`.

## CI/CD

Pipeline shape: unit tests → `sam build` → `sam validate --lint` →
`sam deploy --no-confirm-changeset --no-fail-on-empty-changeset` per stage,
authenticated via an OIDC role, not long-lived keys. Keep one
template/config per environment via `samconfig.toml` profiles
(`sam deploy --config-env prod`) or separate parameter files. `sam
pipeline init` scaffolds GitHub Actions/GitLab/Jenkins pipelines including
the OIDC roles.

## Code-only pushes to an existing function

For a function not (yet) under IaC, or emergency patching:

```bash
zip -r fn.zip app.py
aws lambda update-function-code --function-name orders --zip-file fileb://fn.zip
aws lambda update-function-configuration --function-name orders --timeout 60
aws lambda get-function --function-name orders --query Configuration.LastUpdateStatus
```

Updates are asynchronous — wait for `LastUpdateStatus: Successful` (or `aws
lambda wait function-updated-v2`) before invoking, and expect
`ResourceConflictException` if you fire config+code updates back-to-back.
If the function *is* IaC-managed, push through the IaC — direct updates
drift and get silently reverted on the next deploy.
