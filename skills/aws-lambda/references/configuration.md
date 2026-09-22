# Configuration, performance, and operations

## Memory, CPU, and timeout sizing

Memory is the only performance dial: CPU, network, and I/O scale linearly
with it (~1 vCPU at 1,769 MB, up to 6 at 10,240 MB). CPU-bound code often
gets *cheaper* at higher memory because duration drops faster than the
per-GB-second price rises — don't hand-tune, run
[aws-lambda-power-tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
(a Step Functions app that invokes at several sizes and charts cost vs
speed). Start at 512 MB for anything non-trivial; the 128 MB default
strangles even JSON parsing. Read actuals from the `REPORT` log line
(`Max Memory Used`, `Billed Duration`).

Set timeout to a bit above the *observed* p99, not the 900 s max: a hung
downstream call should fail in seconds, and for queue sources the
visibility timeout must exceed the function timeout. Default to `arm64`
(Graviton, ~20% cheaper per GB-second); choose x86_64 only for binaries
without arm builds.

## Cold starts

A cold start = environment provisioning + runtime start + your init code;
it hits the first invocation on a new environment (new deploys, scale-up,
idle reaping). Order of remedies:

1. **Trim init**: smaller bundles (tree-shake/esbuild for Node), import only
   needed SDK clients, lazy-import heavy libs used on rare paths.
2. **SnapStart** (Java, Python 3.12+, .NET 8+): snapshots the initialised
   environment and resumes from it — near-eliminates init cost for heavy
   runtimes. Attaches to published versions. Caveat: init-time state is
   snapshotted, so seed randomness/uniqueness (and refresh short-lived
   creds/connections) in the handler or a restore hook, not at init.
3. **Provisioned concurrency**: keeps N environments warm; the only hard
   latency guarantee. Costs while idle — attach to an alias, scale on a
   schedule (business hours) via Application Auto Scaling.

Ping-style warmers are a hack that keeps one environment warm and does
nothing under concurrent load; prefer the above.

## Concurrency and throttling

Every in-flight invocation consumes one unit of the account's regional pool
(default 1,000; raisable). Throttles surface as 429s (sync), silent
retries (async), or a stalled queue (pollers). Two per-function controls:

- **Reserved concurrency** — a cap and a carve-out. Use it to protect a
  fragile downstream (cap DB-writing functions at what the DB tolerates) or
  guarantee headroom for a critical function. Setting it to 0 is the kill
  switch for a runaway function.
- **SQS `MaximumConcurrency`** (on the event source mapping) — caps how many
  environments one queue drives without capping the function globally;
  prefer it over reserved concurrency for queue workers.

Kinesis/DynamoDB stream concurrency = shard count × `ParallelizationFactor`;
scale shards, not memory, when a stream backs up.

## Environment variables and secrets

Env vars (4 KB total, per-version snapshot) are for plain config — table
names, feature flags, log level. Secrets and anything rotated belong in
**Secrets Manager** or **SSM Parameter Store**, fetched at init and cached;
the [AWS Parameters and Secrets Lambda extension](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)
(a layer) does the caching for you, as do Powertools' `parameters` utilities
with TTL. Never commit secrets into template `Environment:` blocks —
reference dynamically (`{{resolve:secretsmanager:...}}`) or fetch at
runtime; remember rotation only works if the function re-fetches (TTL), not
init-once-forever.

## VPC networking

Attach to a VPC only to reach private resources. Consequences to handle:
no internet egress without a NAT gateway in a routed subnet; AWS APIs need
NAT or VPC endpoints (gateway endpoints for S3/DynamoDB are free — use
them); DNS of peered/on-prem resources needs resolver rules. Use **RDS
Proxy** in front of RDS — Lambda's scale-out otherwise exhausts database
connections, and IAM auth via the proxy removes DB passwords. ENI creation
is amortised (Hyperplane) so VPC no longer adds seconds to every cold
start, but subnets need free IPs to scale.

## Observability

- **Structured logs.** Emit JSON (Lambda's JSON log format setting, or
  Powertools Logger which injects `cold_start`, function metadata, and the
  correlation id). Always log the failing *input identifiers* (not whole
  payloads/PII) so a DLQ message can be traced back. Set log retention
  explicitly (`RetentionInDays`) — default is never-expire and billed.
- **Metrics.** Alarm on `Errors` (>0 over N periods), `Throttles`,
  `DurationP99` approaching timeout, DLQ/failure-destination depth, and
  `IteratorAge` for stream pollers (the backlog signal). Powertools Metrics
  writes custom metrics via EMF (no API calls, no latency).
- **Tracing.** Enable X-Ray (`Tracing: Active`) or wire OpenTelemetry via
  the ADOT layer; Powertools Tracer annotates cold starts and captures
  SDK calls per segment.
- **[Lambda Powertools](https://docs.powertools.aws.dev/)** (Python,
  TypeScript, Java, .NET) is the default answer for logging, metrics,
  tracing, idempotency (DynamoDB-backed decorator), batch processing, and
  parameter caching — reach for it before writing any of those by hand.

## Cost model

Price = requests + GB-seconds (memory × billed duration), plus provisioned
concurrency while allocated. Free-ish tier aside, the usual cost bugs:
over-provisioned memory on I/O-bound functions that wait, chatty functions
invoked per record instead of per batch, `Errors`-driven retry storms,
CloudWatch log ingestion from debug-level logging in prod, and idle
provisioned concurrency running 24/7 for a business-hours workload.
