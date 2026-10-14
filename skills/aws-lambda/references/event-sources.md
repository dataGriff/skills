# Event sources: shapes, semantics, failure handling

Three invocation models decide retry behaviour; identify the model before
reasoning about failures.

| Model | Sources | On error |
| --- | --- | --- |
| Synchronous | API Gateway, function URLs, ALB, direct `Invoke` | Caller gets the error; no Lambda-side retry |
| Asynchronous | S3, SNS, EventBridge, `InvocationType=Event` | Lambda queues the event, retries 2× (~1 min, ~2 min apart), then discards or routes to a failure destination |
| Event source mapping (poller) | SQS, DynamoDB Streams, Kinesis, Kafka/MQ | Lambda polls and invokes with batches; retry behaviour is per source (below) |

## HTTP: API Gateway and function URLs

Function URLs and HTTP API (v2) use the same payload: method in
`event.requestContext.http.method`, path params in `event.pathParameters`,
body as a **string** in `event.body` (base64 when `isBase64Encoded`) — always
`json.loads`/`JSON.parse` it. REST API (v1) differs: `event.httpMethod`,
`event.path`. Respond with:

```json
{ "statusCode": 201, "headers": {"Content-Type": "application/json"}, "body": "{\"id\": \"...\"}" }
```

A bare object return from a v2/function-URL handler is auto-serialised as a
200, but be explicit once you need status codes. Gotchas: API Gateway caps
integration time at 29 s regardless of function timeout (function URLs
don't); header keys arrive lowercased; use function URLs for simple
invoke-over-HTTP, API Gateway when you need auth beyond IAM, usage plans,
custom domains with WAF, or request validation.

## SQS

Batch of up to 10 messages (up to 10,000 with `MaxBatchingWindow` for
high-throughput): payload in `Records[].body` (string — parse it), metadata
in `messageId`, `receiptHandle`, `messageAttributes`. On clean return Lambda
deletes the batch; on throw the **whole batch** returns to the queue.

Always enable partial batch responses so one bad message doesn't recycle
nine good ones — `FunctionResponseTypes: [ReportBatchItemFailures]` in
SAM/event source mapping, then:

```python
def handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            process(json.loads(record["body"]))
        except Exception:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}
```

Returning `{"batchItemFailures": []}` means all succeeded. Configure a
**redrive policy (DLQ) on the queue itself** (`maxReceiveCount` 3–5) — a
poisoned message otherwise retries until the 14-day retention expires. Set
queue `VisibilityTimeout` ≥ function timeout (AWS recommends 6×). FIFO
queues: one failure blocks the whole message group, by design.

## S3

`Records[].s3.bucket.name` and `Records[].s3.object.key` — the key is
URL-encoded (`+` for spaces): decode with `urllib.parse.unquote_plus`
before `GetObject` or keys with spaces 404. Async model, so wire an
`OnFailure` destination. Two loop/consistency traps: writing output to the
triggering bucket without a prefix filter recurses infinitely (Lambda
detects and can throttle recursive loops, but don't rely on it); events for
rapid overwrites of the same key can arrive out of order — use the object
`versionId`/`sequencer` if order matters.

## EventBridge (CloudWatch Events)

Your data is in `event.detail` (already an object, not a string), with
`source` and `detail-type` for routing. Scheduled rules
(`rate(5 minutes)` / `cron(...)`, or Scheduler) deliver a near-empty event —
the function should carry its own context. Async model: retries 2×, so
scheduled jobs must be idempotent; set an `OnFailure` destination or the
rule's DLQ.

## SNS

One record per invoke — `Records[0].Sns.Message` (string, parse if JSON).
Async retries apply; for fan-out where you need buffering or batching,
prefer SNS → SQS → Lambda over SNS → Lambda.

## DynamoDB Streams and Kinesis

Ordered, sharded batches: records in `Records[].dynamodb`
(`NewImage`/`OldImage` in DynamoDB JSON — unmarshal with
`boto3.dynamodb.types.TypeDeserializer` or `@aws-sdk/util-dynamodb
unmarshall`) or `Records[].kinesis.data` (base64). A throwing batch is
retried **until it expires (24 h) and blocks its whole shard** — the
poison-pill scenario. Mitigate on the event source mapping:
`MaximumRetryAttempts`, `BisectBatchOnFunctionError: true`, an `OnFailure`
destination (SQS/SNS, receives record metadata, not the data), and
`ReportBatchItemFailures` (return the **lowest** failed sequence number;
Lambda retries from there).

## Failure destinations vs DLQs

Prefer **destinations** (`OnFailure` → SQS/SNS/EventBridge/another Lambda)
over the legacy `DeadLetterConfig` for async sources: destinations capture
the full invocation record including the error, and `OnSuccess` exists for
chaining without writing glue code. Queue-side redrive DLQs remain correct
for SQS (the failure config lives on the queue, not the function). Whatever
captures failures, something must *consume* it — an alarm on DLQ depth at
minimum.

## Testing events

`sam local generate-event s3 put`, `... sqs receive-message`, etc. produce
realistic payloads for `sam local invoke -e`. In unit tests, build small
dict/object fixtures per shape above rather than recording full console
samples.
