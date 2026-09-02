---
name: aws-lambda
description: >-
  Build, configure, deploy, and debug AWS Lambda functions: handler patterns
  per runtime, packaging (zip/container), infrastructure-as-code with SAM,
  CDK, or Terraform, event source wiring (API Gateway, function URLs, SQS,
  S3, EventBridge, DynamoDB/Kinesis streams), IAM execution roles,
  retries/DLQs/idempotency, cold starts, concurrency, and observability. Use
  when the user mentions AWS Lambda, a lambda function/handler, serverless
  functions on AWS, SAM or `sam local`, function URLs, Lambda layers, event
  source mappings, provisioned concurrency or SnapStart, or asks to write,
  deploy, trigger, optimise, or troubleshoot code running in Lambda.
---

# AWS Lambda

Lambda runs a handler function in a managed, ephemeral execution
environment. Everything that goes wrong in Lambda work traces back to a few
realities: environments are reused but never guaranteed, invocations retry,
resources are capped, and the function's IAM role decides what it can touch.
Design for those from the start instead of retrofitting.

## Handler rules

Initialise once, outside the handler. The init phase (code outside the
handler) runs only on cold start and gets a full-CPU burst; the execution
environment — and anything cached in it — is reused across warm invocations.
Create SDK clients, DB connections, and load config/secrets at init scope,
never per invocation:

```python
import boto3

table = boto3.resource("dynamodb").Table("orders")  # init: once per environment

def handler(event, context):        # invoke: once per request
    table.put_item(Item={"pk": event["orderId"], "status": "received"})
    return {"statusCode": 200}
```

```javascript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
const client = new DynamoDBClient({});          // init scope

export const handler = async (event, context) => { /* per request */ };
```

- **Stateless between invocations.** Reused state is a cache, not a store —
  it vanishes without notice. Persist anything that matters (DynamoDB, S3);
  `/tmp` is scratch space only.
- **Idempotent always.** Async invokes retry twice on error; SQS and stream
  sources redeliver; at-least-once delivery is the norm. Key writes on a
  natural id (order id, message id) so a retry is a no-op.
- **Return/raise deliberately.** Throwing signals failure and triggers the
  source's retry policy; swallowing an exception marks the batch/record
  processed. Decide which you mean per error, don't let it fall out.
- **Never spawn work past the return.** Background promises/threads are
  frozen when the invocation ends. Await everything; hand slow work to SQS.
- **Read the payload for what it is.** Each trigger wraps your data
  differently (API Gateway stringifies the body, SQS nests it in
  `Records[].body`, EventBridge in `detail`). Open
  [references/event-sources.md](references/event-sources.md) whenever you
  wire or parse a trigger — shapes, retry semantics, and batching live there.

## Project and deployment

Define the function as infrastructure-as-code — SAM, CDK, Terraform, or
Serverless Framework, matching whatever the repo already uses. Console-made
or one-off `aws lambda create-function` setups drift and can't be reviewed.
For a fresh project default to SAM; a minimal template:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Resources:
  OrdersFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler          # file.function
      Runtime: python3.13
      CodeUri: src/
      Architectures: [arm64]        # cheaper; use x86_64 only for native deps that need it
      Timeout: 30                   # default 3s is a trap; max 900
      MemorySize: 512               # CPU scales with memory
      Policies:
        - DynamoDBCrudPolicy: { TableName: !Ref OrdersTable }
      Events:
        Api:
          Type: HttpApi
          Properties: { Path: /orders, Method: post }
```

`sam build && sam deploy --guided` ships it; `sam build && sam local invoke
-e event.json` runs it locally in a Lambda-like container, and
`sam local start-api` serves HTTP triggers. Pin the runtime to a current
version (python3.13, nodejs22.x, java21, dotnet8, provided.al2023 for
Go/Rust) — deprecated runtimes block updates.

For CDK/Terraform equivalents, container-image packaging, layers,
versions/aliases and gradual (canary) deploys, CI/CD wiring, or quick
code-only pushes to an existing function, open
[references/deployment.md](references/deployment.md).

## Permissions

Two directions, always distinct:

- **Execution role** — what the *function* may call. One role per function,
  scoped to the exact tables/buckets/queues it touches (SAM policy templates
  like `DynamoDBCrudPolicy` above do this cleanly). Never attach
  `AdministratorAccess` or `*` resource policies to get unblocked; add the
  specific missing action the AccessDenied error names.
- **Resource-based policy** — who may *invoke* the function
  (`lambda:InvokeFunction` grants for S3, EventBridge, other accounts). SAM
  `Events`/CDK grants create these; hand-rolled Terraform needs an explicit
  `aws_lambda_permission`.

The role also needs `AWSLambdaBasicExecutionRole` (CloudWatch Logs) — SAM
adds it implicitly; plain IAC must include it or the function logs nothing.

## Limits that shape design

| Limit | Value |
| --- | --- |
| Timeout | 900 s max (default 3 s) |
| Memory / CPU | 128–10,240 MB; CPU scales with memory (~1 vCPU ≈ 1769 MB) |
| Payload | 6 MB sync, 256 KB async |
| Package | 50 MB zipped / 250 MB unzipped (with layers); 10 GB container image |
| `/tmp` | 512 MB default, configurable to 10 GB |
| Env vars | 4 KB total |
| Concurrency | shared account pool (default 1,000) |

Work that can exceed these belongs elsewhere: >15 min → Step Functions or
ECS/Fargate; >6 MB responses → presigned S3 URLs or response streaming;
huge deps → container image.

## Pitfalls worth checking for

- **Recursive loops.** A function writing to the bucket/queue/topic that
  triggers it invokes itself forever. Filter events (prefix/suffix, message
  attributes) or write elsewhere.
- **Timeout mismatches.** Queue visibility timeout below function timeout
  causes duplicate processing (set it ≥ the function timeout, AWS suggests
  6×); SDK client timeouts defaulting higher than the function timeout hide
  the real error as a generic `Task timed out`.
- **VPC attachment by reflex.** Only attach to a VPC to reach private
  resources (RDS, ElastiCache); a VPC function has no internet without a NAT
  gateway, and DynamoDB/S3/etc. need gateway/interface endpoints.
- **Debugging from guesses.** The truth is in CloudWatch: the log line
  `REPORT ... Duration / Max Memory Used` tells you about timeouts and
  memory pressure; a `Task timed out` with no traceback means raise the
  timeout or find the hang, not add try/except.

When tuning performance or cost (cold starts, provisioned concurrency,
SnapStart, memory sizing), managing concurrency, handling secrets, or
setting up structured logging/tracing (Powertools), open
[references/configuration.md](references/configuration.md).

## References

- [references/event-sources.md](references/event-sources.md) — open when
  wiring or parsing a trigger: event shapes per source, sync/async/poller
  semantics, retries, DLQs and failure destinations, SQS/stream batching and
  partial batch responses.
- [references/deployment.md](references/deployment.md) — open when
  packaging or shipping: SAM/CDK/Terraform patterns, container images,
  layers, versions/aliases and canary deploys, `sam local` workflows, CI/CD.
- [references/configuration.md](references/configuration.md) — open when
  tuning or operating: memory/timeout sizing, cold starts, SnapStart,
  provisioned/reserved concurrency, env vars and secrets, VPC networking,
  observability with Powertools.
