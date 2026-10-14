# Testing and CI

For writing `terraform test` suites, runtime checks, and pipelines.

## The validation ladder

Cheapest first; each step catches what the previous can't:

1. `terraform fmt -check -recursive` — formatting.
2. `terraform validate` — syntax, types, references. Needs `terraform init`
   first; use `init -backend=false` in CI jobs that shouldn't touch state.
3. `tflint` — provider-aware lint (invalid instance types, deprecated
   syntax, unused declarations). Configured via `.tflint.hcl`; run
   `tflint --init` to fetch rulesets.
4. Security scanners — `trivy config .` or `checkov -d .` for
   misconfigurations (open security groups, unencrypted storage).
5. `terraform test` — behavioural tests of your logic (below).
6. `terraform plan` against real state — the only step that sees reality.

## terraform test (>= 1.6)

Tests live in `tests/*.tftest.hcl` next to the module. Each `run` block is
a plan (default on 1.7+... set explicitly for clarity) or a real apply;
apply-mode runs create and then destroy real infrastructure, so default to
`command = plan` and reserve apply for modules with dedicated sandbox
accounts.

```hcl
# tests/naming.tftest.hcl
variables {                       # file-wide defaults for required inputs
  project     = "demo"
  environment = "dev"
}

run "bucket_name_is_prefixed" {
  command = plan

  assert {
    condition     = startswith(aws_s3_bucket.this.bucket, "demo-dev-")
    error_message = "Bucket name must start with <project>-<environment>-."
  }
}

run "rejects_bad_environment" {
  command = plan
  variables { environment = "production" }   # override per-run
  expect_failures = [var.environment]        # the validation should trip
}
```

- `expect_failures` asserts that a specific variable validation,
  precondition, or check fails — how you test your guardrails.
- `run` blocks can chain: a later block can reference an earlier one's
  outputs (`run.setup.bucket_name`) to test wiring between modules.
- Mock providers (>= 1.7) let plan-time tests run with no credentials:

```hcl
mock_provider "aws" {
  mock_resource "aws_s3_bucket" {
    defaults = { arn = "arn:aws:s3:::mock" }
  }
}
```

- Run with `terraform test`, one module at a time, after `init`.

## Runtime assertions in the config itself

- `variable.validation` — reject bad inputs at plan time (see SKILL.md).
- `precondition` (in a resource/data `lifecycle`) — assert an assumption
  before create: e.g. the looked-up AMI is actually x86_64.
- `postcondition` — assert a result after create/read: e.g. the
  certificate really covers the domain. `self` refers to the resource.
- `check` blocks — continuous, **non-blocking** assertions (a failing
  check warns but doesn't stop apply); good for "endpoint responds",
  "cert not near expiry".

```hcl
check "health" {
  data "http" "app" { url = "https://${aws_lb.this.dns_name}/health" }
  assert {
    condition     = data.http.app.status_code == 200
    error_message = "App health endpoint is not returning 200."
  }
}
```

## CI/CD shape

PRs get a plan; only trusted branches apply:

- **On PR**: fmt-check → init → validate → tflint/scanners →
  `terraform plan -out=tfplan -input=false -lock-timeout=5m`, post the
  plan (or `show -no-color tfplan`) as a PR comment for review.
- **On merge to main** (or manual approval gate): re-plan and apply, or
  apply the artifact plan. A saved plan is only valid against the state
  version it was made from — if anything applied in between, re-plan.
- **Nightly**: `terraform plan -detailed-exitcode` per root module; exit
  code 2 means drift/pending changes — alert, don't auto-apply.
- Useful flags in automation: `-input=false`, `-no-color`,
  `-detailed-exitcode` (0 clean / 1 error / 2 changes), `TF_IN_AUTOMATION=1`.

Security notes: plan files and `show -json` output contain sensitive
values — treat plan artifacts like secrets, don't post raw JSON plans to
public PRs. Give CI credentials via OIDC/workload identity, not long-lived
keys; the apply role is the most powerful credential in the org, so gate
it (environment protection rules, manual approval) and scope per root
module where possible.
